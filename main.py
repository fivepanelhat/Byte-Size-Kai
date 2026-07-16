"""
Byte Size Kai - Main Orchestrator with Full Data Flywheel Integration

Edge optimisations (RPi 5 16GB + Hailo-10H friendly):
- Exception-safe multimodal gather
- Plan rate limiting (avoid LLM/GPIO thrash)
- Latest-sensor coalescing
- Optional adaptive AV (skip when sensors stable)
- Background media pruner
- Bounded flywheel log rotation
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from coastal_alpine_core.portal_core import (
    load_bluemoon_config,
    AIAgent,
    MQTTClient,
    AVCapture,
    MediaPruner,
    HardwareController,
)
from coastal_alpine_core import DataFlywheel

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ByteSizeKai")

# Loop / edge policy (overridable via env)
MIN_PLAN_INTERVAL_SEC = float(os.getenv("BLUE_MOON_MIN_PLAN_INTERVAL_SEC", "30"))
ADAPTIVE_AV = os.getenv("BLUE_MOON_ADAPTIVE_AV", "false").lower() in (
    "1",
    "true",
    "yes",
)
ENABLE_MEDIA_RECORDING = os.getenv("ENABLE_MEDIA_RECORDING", "true").lower() in (
    "1",
    "true",
    "yes",
)
FLYWHEEL_MAX_BYTES = int(os.getenv("BLUE_MOON_FLYWHEEL_MAX_BYTES", str(5 * 1024 * 1024)))
FLYWHEEL_KEEP_LINES = int(os.getenv("BLUE_MOON_FLYWHEEL_KEEP_LINES", "2000"))
MQTT_READ_TIMEOUT_SEC = float(os.getenv("BLUE_MOON_MQTT_TIMEOUT_SEC", "5"))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def rotate_flywheel_if_needed(
    path: str | Path,
    max_bytes: int = FLYWHEEL_MAX_BYTES,
    keep_lines: int = FLYWHEEL_KEEP_LINES,
) -> None:
    """Trim JSONL flywheel when it grows too large (SD-card safe)."""
    p = Path(path)
    if not p.is_file():
        return
    try:
        if p.stat().st_size <= max_bytes:
            return
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        if len(lines) <= keep_lines:
            # Size large but few lines — keep last half of file by bytes approx
            data = p.read_bytes()
            p.write_bytes(data[-max_bytes // 2 :])
            logger.warning("Flywheel rotated by size trim: %s", p)
            return
        kept = lines[-keep_lines:]
        p.write_text("\n".join(kept) + "\n", encoding="utf-8")
        logger.warning(
            "Flywheel rotated: kept last %d lines (max_bytes=%d)",
            keep_lines,
            max_bytes,
        )
    except OSError as e:
        logger.error("Flywheel rotation failed: %s", e)


def _is_stable_status(analysis: Any) -> bool:
    if analysis is None or isinstance(analysis, Exception):
        return False
    if isinstance(analysis, dict):
        status = str(analysis.get("status", "")).lower()
        return status in ("healthy", "optimal", "ok", "stable", "normal")
    status = str(getattr(analysis, "status", "")).lower()
    return status in ("healthy", "optimal", "ok", "stable", "normal")


class ByteSizeKaiPortal:
    """Byte Size Kai edge orchestrator."""

    def __init__(self, config):
        self.config = config
        self.flywheel_path = "flywheel_blue_moon.jsonl"
        self.flywheel = DataFlywheel(storage_path=self.flywheel_path)

        self.ai_agent = AIAgent(
            ollama_host=config.ollama.host,
            model=config.ollama.model,
            flywheel=self.flywheel,
        )
        self.mqtt_client = MQTTClient(
            broker_host=config.mqtt.broker,
            broker_port=config.mqtt.port,
            client_id="blue-moon-portal",
            username=config.mqtt.username,
            password=config.mqtt.password,
            topic_prefix=getattr(config.mqtt, "topic_prefix", "horowhenua/sensors"),
        )
        self.av_capture = AVCapture(
            camera_index=config.camera.device_index,
            video_fps=config.camera.fps,
            audio_sample_rate=config.audio.sample_rate,
            audio_chunk_size=config.audio.chunk_size,
        )
        storage = config.storage
        compliance_dir = str(getattr(storage, "compliance_dir", "") or "")
        self.media_pruner = MediaPruner(
            media_dir=str(storage.media_dir),
            sensor_logs_dir=str(storage.sensor_logs_dir),
            compliance_dir=compliance_dir,
            retention_hours=storage.retention_hours,
            critical_disk_usage_pct=storage.critical_disk_usage_pct,
        )
        # Prefer full config object; kwargs still work for older core versions
        try:
            self.hardware_control = HardwareController(config=config)
        except TypeError:
            self.hardware_control = HardwareController(
                pump_gpio_pin=config.hardware.pump_gpio_pin,
                pump_pwm_frequency=config.hardware.pump_pwm_frequency,
                lighting_gpio_pin=config.hardware.lighting_gpio_pin,
                lighting_pwm_frequency=config.hardware.lighting_pwm_frequency,
                alert_gpio_pin=config.hardware.alert_gpio_pin,
                simulation_mode=not config.hardware.enable_hardware_control,
            )

        self.is_running = False
        self._tasks: list[asyncio.Task] = []
        self._last_plan_at: Optional[float] = None
        self._latest_sensor: Optional[Dict[str, Any]] = None
        self._loop = None

        logger.info(
            "Byte Size Kai initialized (model=%s, adaptive_av=%s, min_plan_interval=%ss)",
            config.ollama.model,
            ADAPTIVE_AV,
            MIN_PLAN_INTERVAL_SEC,
        )

    # ----- lifecycle helpers used by tests / hardware adapters -----

    async def setup(self) -> None:
        """Optional hardware setup hook (tests may mock hardware_control.setup)."""
        setup = getattr(self.hardware_control, "setup", None)
        if setup is not None:
            result = setup()
            if asyncio.iscoroutine(result):
                await result

    async def cleanup(self) -> None:
        cleanup = getattr(self.hardware_control, "cleanup", None)
        if cleanup is not None:
            result = cleanup()
            if asyncio.iscoroutine(result):
                await result

    async def health_check(self) -> Dict[str, bool]:
        checks = {}
        for name, comp in (
            ("ai_agent", self.ai_agent),
            ("mqtt_client", self.mqtt_client),
            ("av_capture", self.av_capture),
            ("hardware_control", self.hardware_control),
        ):
            fn = getattr(comp, "health_check", None)
            if fn is None:
                checks[name] = True
                continue
            try:
                result = fn()
                if asyncio.iscoroutine(result):
                    result = await result
                checks[name] = bool(result)
            except Exception as e:
                logger.warning("Health check failed for %s: %s", name, e)
                checks[name] = False
        return checks

    async def process_sensor_loop(self):
        """Main closed-loop: MQTT → multimodal AI → plan → actuate → flywheel."""
        while self.is_running:
            try:
                message = await asyncio.wait_for(
                    self.mqtt_client.read_message(),
                    timeout=MQTT_READ_TIMEOUT_SEC,
                )

                # Coalesce: keep latest payload (also allows bursty brokers)
                if isinstance(message, dict):
                    self._latest_sensor = message
                else:
                    continue

                payload = self._latest_sensor.get("payload", self._latest_sensor)

                # Rate-limit full planning (first event always runs)
                now = asyncio.get_event_loop().time()
                if (
                    self._last_plan_at is not None
                    and (now - self._last_plan_at) < MIN_PLAN_INTERVAL_SEC
                ):
                    logger.debug(
                        "Skipping plan (rate limit %.1fs)", MIN_PLAN_INTERVAL_SEC
                    )
                    continue

                analysis = await self.ai_agent.analyze_sensor_state(
                    sensor_data=payload
                )

                # Multimodal capture (exception-safe)
                frame, audio = None, None
                want_av = ENABLE_MEDIA_RECORDING
                if ADAPTIVE_AV and _is_stable_status(analysis):
                    # Still allow AV periodically via rate limit window
                    want_av = False
                    logger.debug("Adaptive AV: sensors stable — skipping capture")

                if want_av:
                    frame_res, audio_res = await asyncio.gather(
                        self.av_capture.capture_frame(),
                        self.av_capture.capture_audio_chunk(),
                        return_exceptions=True,
                    )
                    if isinstance(frame_res, Exception):
                        logger.warning("Frame capture failed: %s", frame_res)
                        frame = None
                    else:
                        frame = frame_res
                    if isinstance(audio_res, Exception):
                        logger.warning("Audio capture failed: %s", audio_res)
                        audio = None
                    else:
                        audio = audio_res

                visual_analysis, audio_analysis = None, None
                if want_av:
                    visual_analysis, audio_analysis = await asyncio.gather(
                        self.ai_agent.process_visual_feedback(frame_data=frame),
                        self.ai_agent.process_audio_feedback(audio_data=audio),
                        return_exceptions=True,
                    )
                    if isinstance(visual_analysis, Exception):
                        logger.warning("Visual analysis failed: %s", visual_analysis)
                        visual_analysis = {"status": "unavailable", "error": str(visual_analysis)}
                    if isinstance(audio_analysis, Exception):
                        logger.warning("Audio analysis failed: %s", audio_analysis)
                        audio_analysis = {"status": "unavailable", "error": str(audio_analysis)}

                plan = await self.ai_agent.generate_optimization_plan(
                    sensor_analysis=analysis,
                    visual_analysis=visual_analysis,
                    audio_analysis=audio_analysis,
                )

                logger.info("Generated optimization plan: %s", plan)
                self._last_plan_at = asyncio.get_event_loop().time()

                if plan and (isinstance(plan, dict) and plan.get("plan_id") or plan):
                    plan_dict = plan if isinstance(plan, dict) else {"plan_id": str(plan)}
                    enforcement_ok = await self.hardware_control.enforce_plan(plan_dict)

                    action = (
                        plan_dict.get("pump_action")
                        or plan_dict.get("lighting_action")
                        or "unknown"
                    )
                    if hasattr(self.ai_agent, "record_hardware_result"):
                        self.ai_agent.record_hardware_result(
                            plan_id=plan_dict.get("plan_id", "unknown"),
                            action=str(action),
                            success=bool(enforcement_ok),
                            metadata={
                                "pump_action": plan_dict.get("pump_action"),
                                "lighting_action": plan_dict.get("lighting_action"),
                                "confidence_score": plan_dict.get("confidence_score"),
                                "ts": _utcnow().isoformat(),
                            },
                        )

                    if enforcement_ok:
                        logger.info(
                            "Plan enforced successfully: %s",
                            plan_dict.get("plan_id"),
                        )
                    else:
                        logger.error(
                            "Plan enforcement failed: %s", plan_dict.get("plan_id")
                        )

                    rotate_flywheel_if_needed(self.flywheel_path)

            except asyncio.TimeoutError:
                # Idle broker — continue waiting
                pass
            except asyncio.CancelledError:
                logger.info("Sensor loop cancelled")
                break
            except Exception as e:
                logger.error("Sensor processing error: %s", e, exc_info=True)
                await asyncio.sleep(1)

    async def _pruner_loop(self):
        """Run media pruner in background (hourly cycle lives inside MediaPruner.start)."""
        try:
            await self.media_pruner.start()
        except asyncio.CancelledError:
            await self.media_pruner.stop()
            raise

    async def start(self) -> None:
        """Connect subsystems and run forever until stop()."""
        if self.is_running:
            return

        await self.setup()
        connected = await self.mqtt_client.connect()
        if not connected:
            logger.warning("MQTT connect failed — continuing (will retry on read)")

        try:
            await self.av_capture.start_video_stream()
        except Exception as e:
            logger.warning("Video stream start failed: %s", e)
        try:
            await self.av_capture.start_audio_stream()
        except Exception as e:
            logger.warning("Audio stream start failed: %s", e)

        self.is_running = True
        self._tasks = [
            asyncio.create_task(self.process_sensor_loop(), name="sensor_loop"),
            asyncio.create_task(self._pruner_loop(), name="media_pruner"),
        ]
        logger.info("Byte Size Kai started")
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def stop(self) -> None:
        """Graceful shutdown."""
        self.is_running = False
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        try:
            await self.media_pruner.stop()
        except Exception:
            pass
        try:
            await self.av_capture.stop()
        except Exception:
            pass
        try:
            await self.mqtt_client.disconnect()
        except Exception:
            pass
        await self.cleanup()
        logger.info("Byte Size Kai stopped")


# Back-compat aliases (pre-rename Blue Moon Portal)
BlueMoonPortal = ByteSizeKaiPortal
BlueMonPortal = ByteSizeKaiPortal


async def _amain() -> int:
    try:
        config = load_bluemoon_config()
    except Exception as e:
        logger.error("Failed to load configuration: %s", e)
        return 1

    portal = ByteSizeKaiPortal(config)
    loop = asyncio.get_running_loop()

    def _signal_handler():
        logger.info("Shutdown signal received")
        asyncio.create_task(portal.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Windows
            signal.signal(sig, lambda *_: asyncio.create_task(portal.stop()))

    try:
        await portal.start()
    except KeyboardInterrupt:
        await portal.stop()
    return 0


def main() -> None:
    try:
        raise SystemExit(asyncio.run(_amain()))
    except KeyboardInterrupt:
        logger.info("Interrupted")
        raise SystemExit(0)


if __name__ == "__main__":
    main()
