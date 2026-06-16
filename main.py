"""
Blue Moon Portal - Main Orchestrator with Full Data Flywheel Integration

Hardware outcomes are now automatically recorded to the flywheel after enforcement.
"""

import asyncio
import logging
import sys
import signal
from datetime import datetime

from portal_core.config import load_config, print_config
from portal_core.ai_agent import AIAgent
from portal_core.mqtt_client import MQTTClient
from portal_core.av_capture import AVCapture
from portal_core.media_pruner import MediaPruner
from portal_core.hardware_control import HardwareControl

from coastal_alpine_core.flywheel import DataFlywheel

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
    def __init__(self, config):
        self.config = config

        # Initialize flywheel for this portal
        self.flywheel = DataFlywheel(storage_path="flywheel_blue_moon.jsonl")

        self.ai_agent = AIAgent(
            ollama_host=config.ollama.host,
            model=config.ollama.model,
            flywheel=self.flywheel,   # Pass flywheel for full integration
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
        logger.info("Blue Moon Portal orchestrator initialized with full flywheel support")

    async def process_sensor_loop(self):
        while self.is_running:
            try:
                message = await asyncio.wait_for(
                    self.mqtt_client.read_message(), timeout=5.0
                )

                analysis = await self.ai_agent.analyze_sensor_state(sensor_data=message["payload"])

                frame, audio = await asyncio.gather(
                    self.av_capture.capture_frame(),
                    self.av_capture.capture_audio_chunk(),
                    return_exceptions=True,
                )

                visual_analysis, audio_analysis = await asyncio.gather(
                    self.ai_agent.process_visual_feedback(frame_data=frame),
                    self.ai_agent.process_audio_feedback(audio_data=audio),
                    return_exceptions=True,
                )

                plan = await self.ai_agent.generate_optimization_plan(
                    sensor_analysis=analysis,
                    visual_analysis=visual_analysis,
                    audio_analysis=audio_analysis,
                )

                logger.info(f"Generated optimization plan: {plan}")

                # Enforce hardware actions + record outcome to flywheel
                if plan and "plan_id" in plan:
                    enforcement_ok = await self.hardware_control.enforce_plan(plan)

                    # === COMPLETE FLYWHEEL HARDWARE OUTCOME RECORDING ===
                    action = plan.get("pump_action") or plan.get("lighting_action") or "unknown"
                    self.ai_agent.record_hardware_result(
                        plan_id=plan.get("plan_id"),
                        action=action,
                        success=enforcement_ok,
                        metadata=plan
                    )

                    if enforcement_ok:
                        logger.info(f"Plan enforced successfully: {plan.get('plan_id')}")
                    else:
                        logger.error(f"Plan enforcement failed: {plan.get('plan_id')}")

            except asyncio.TimeoutError:
                pass
            except Exception as e:
                logger.error(f"Sensor processing error: {e}", exc_info=True)
                await asyncio.sleep(1)

    # ... rest of the class (start, stop, health_check, main) unchanged ...
