"""
Blue Moon Portal - Main Orchestrator

Asynchronous event loop that:
1. Connects to MQTT broker for sensor telemetry
2. Manages AV capture streams (CSI camera, microphone)
3. Orchestrates LLM reasoning via Ollama
4. Enforces hardware actions via deterministic commands
5. Runs background media pruning task
"""

import asyncio
import logging
import os
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

from portal_core.config import load_config, print_config
from portal_core.ai_agent import AIAgent
from portal_core.mqtt_client import MQTTClient
from portal_core.av_capture import AVCapture
from portal_core.media_pruner import MediaPruner
from portal_core.hardware_control import HardwareControl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load and validate configuration
try:
    config = load_config()
    print_config(config)
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise


class BlueMonPortal:
    """
    Main orchestrator for Blue Moon Portal.

    Manages AI agent, sensor streams, hardware, and media lifecycle.
    """

    def __init__(self, config):
        """Initialize portal components."""
        self.config = config

        self.ai_agent = AIAgent(
            ollama_host=config.ollama.host,
            model=config.ollama.model,
        )
        self.mqtt_client = MQTTClient(
            broker_host=config.mqtt.broker,
            broker_port=config.mqtt.port,
            client_id="blue-moon-portal",
            username=config.mqtt.username,
            password=config.mqtt.password,
        )
        self.av_capture = AVCapture(
            camera_index=config.camera.device_index,
            video_fps=config.camera.fps,
            audio_sample_rate=config.audio.sample_rate,
            audio_chunk_size=config.audio.chunk_size,
        )
        self.media_pruner = MediaPruner(
            media_dir=str(config.storage.media_dir),
            sensor_logs_dir=str(config.storage.sensor_logs_dir),
            retention_hours=config.storage.retention_hours,
            critical_disk_usage_pct=config.storage.critical_disk_usage_pct,
        )
        self.hardware_control = HardwareControl(
            pump_gpio_pin=config.hardware.pump_gpio_pin,
            pump_pwm_frequency=config.hardware.pump_pwm_frequency,
            lighting_gpio_pin=config.hardware.lighting_gpio_pin,
            lighting_pwm_frequency=config.hardware.lighting_pwm_frequency,
            alert_gpio_pin=config.hardware.alert_gpio_pin,
            simulation_mode=not config.hardware.enable_hardware_control,
        )

        self.is_running = False
        logger.info("Blue Moon Portal orchestrator initialized")

    async def health_check(self) -> dict:
        """
        Verify all subsystems are operational.

        Returns:
            Dict with health status of each component
        """
        logger.info("Running health check...")
        health = {
            "ollama": await self.ai_agent.health_check(),
            "mqtt": await self.mqtt_client.health_check(),
            "av": await self.av_capture.health_check(),
            "hardware": await self.hardware_control.health_check(),
            "timestamp": datetime.now().isoformat(),
        }

        if all(health.values()):
            logger.info("✓ All systems healthy")
        else:
            logger.warning(f"⚠ Health check issues: {health}")

        return health

    async def process_sensor_loop(self):
        """Main sensor processing loop."""
        while self.is_running:
            try:
                # Read MQTT message
                message = await asyncio.wait_for(
                    self.mqtt_client.read_message(), timeout=5.0
                )
                logger.debug(f"Received sensor message: {message['topic']}")

                # Analyze sensor state
                analysis = await self.ai_agent.analyze_sensor_state(
                    sensor_data=message["payload"]
                )

                # Capture visual and audio feedback in parallel
                frame, audio = await asyncio.gather(
                    self.av_capture.capture_frame(),
                    self.av_capture.capture_audio_chunk(),
                    return_exceptions=True,
                )

                # Handle exceptions from capture
                if isinstance(frame, Exception):
                    logger.warning(f"Frame capture error: {frame}")
                    frame = None
                if isinstance(audio, Exception):
                    logger.warning(f"Audio capture error: {audio}")
                    audio = None

                # Process visual and audio in parallel (functions handle None gracefully)
                visual_analysis, audio_analysis = await asyncio.gather(
                    self.ai_agent.process_visual_feedback(frame_data=frame),
                    self.ai_agent.process_audio_feedback(audio_data=audio),
                    return_exceptions=True,
                )

                # Handle exceptions from analysis
                if isinstance(visual_analysis, Exception):
                    logger.warning(f"Visual analysis error: {visual_analysis}")
                    visual_analysis = {}
                if isinstance(audio_analysis, Exception):
                    logger.warning(f"Audio analysis error: {audio_analysis}")
                    audio_analysis = {}

                # Generate optimization plan
                plan = await self.ai_agent.generate_optimization_plan(
                    sensor_analysis=analysis,
                    visual_analysis=visual_analysis,
                    audio_analysis=audio_analysis,
                )

                logger.info(f"Generated optimization plan: {plan}")

                # Enforce hardware actions based on plan
                if plan and "plan_id" in plan:
                    enforcement_ok = await self.hardware_control.enforce_plan(plan)
                    if enforcement_ok:
                        logger.info(
                            f"Plan enforced successfully: {plan.get('plan_id')}"
                        )
                    else:
                        logger.error(f"Plan enforcement failed: {plan.get('plan_id')}")

            except asyncio.TimeoutError:
                # No message within timeout, continue
                pass
            except Exception as e:
                logger.error(f"Sensor processing error: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def start(self):
        """Start the portal."""
        logger.info("Starting Blue Moon Portal...")
        self.is_running = True

        try:
            # Setup hardware control
            await self.hardware_control.setup()

            # Connect to MQTT
            await self.mqtt_client.connect()
            await asyncio.sleep(1)

            # Start AV capture
            video_ok = await self.av_capture.start_video_stream()
            audio_ok = await self.av_capture.start_audio_stream()
            if not (video_ok or audio_ok):
                logger.warning(
                    "No AV streams available (running in telemetry-only mode)"
                )

            # Verify health
            health = await self.health_check()
            if not any(health.values()):
                logger.error("Critical systems offline; cannot proceed")
                return

            # Start media pruner background task
            pruner_task = asyncio.create_task(self.media_pruner.start())

            # Start sensor processing loop
            sensor_task = asyncio.create_task(self.process_sensor_loop())

            logger.info("Blue Moon Portal is ONLINE and processing")

            # Keep running
            await asyncio.gather(pruner_task, sensor_task)

        except Exception as e:
            logger.error(f"Portal startup error: {e}")
            self.is_running = False

    async def stop(self):
        """Gracefully stop the portal."""
        logger.info("Stopping Blue Moon Portal...")
        self.is_running = False

        try:
            await self.media_pruner.stop()
            await self.av_capture.stop()
            await self.mqtt_client.disconnect()
            await self.hardware_control.cleanup()
            logger.info("Blue Moon Portal stopped cleanly")
        except Exception as e:
            logger.error(f"Portal shutdown error: {e}")


async def main():
    """Main entry point."""
    portal = BlueMonPortal(config)

    try:
        await portal.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        await portal.stop()


if __name__ == "__main__":
    asyncio.run(main())
