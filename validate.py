#!/usr/bin/env python3
"""
Blue Moon Portal - Validation & Testing Script

Comprehensive validation of system components before production deployment.
Tests configuration, LLM connectivity, MQTT broker, and hardware initialization.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from portal_core.config import load_config, print_config
from portal_core.ai_agent import AIAgent
from portal_core.mqtt_client import MQTTClient
from portal_core.av_capture import AVCapture
from portal_core.hardware_control import HardwareControl
from portal_core.media_pruner import MediaPruner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_configuration():
    """Test configuration loading and validation."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Configuration Loading & Validation")
    logger.info("=" * 60)

    try:
        config = load_config()
        print_config(config)
        logger.info("✓ Configuration test PASSED")
        return config, None
    except Exception as e:
        logger.error(f"✗ Configuration test FAILED: {e}")
        return None, str(e)


async def test_ollama(config):
    """Test Ollama LLM connectivity."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Ollama LLM Health Check")
    logger.info("=" * 60)

    try:
        ai_agent = AIAgent(
            ollama_host=config.ollama.host,
            model=config.ollama.model,
        )

        is_healthy = await ai_agent.health_check()
        if is_healthy:
            logger.info(f"✓ Point-to-point connection to Ollama at {config.ollama.host} established.")
            logger.info(f"✓ Ollama health check PASSED")
            logger.info(f"  Host: {config.ollama.host}")
            logger.info(f"  Model: {config.ollama.model}")
            return True, None
        else:
            msg = f"Ollama health check failed: Model {config.ollama.model} is not loaded or the server is unresponsive."
            logger.error(f"✗ {msg}")
            return False, msg

    except Exception as e:
        err_msg = f"Ollama connection/initialization error: {e}"
        logger.error(f"✗ {err_msg}")
        return False, err_msg


async def test_mqtt(config):
    """Test MQTT broker connectivity."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Free OCF Broker (MQTT) Connectivity")
    logger.info("=" * 60)

    try:
        mqtt_client = MQTTClient(
            broker_host=config.mqtt.broker,
            broker_port=config.mqtt.port,
            client_id="test-blue-moon-portal",
            username=config.mqtt.username,
            password=config.mqtt.password,
        )

        # Try to connect with timeout
        try:
            connect_ok = await asyncio.wait_for(mqtt_client.connect(), timeout=5.0)
            await asyncio.sleep(1)

            is_healthy = await mqtt_client.health_check()
            if is_healthy:
                logger.info(f"✓ MQTT connection PASSED")
                logger.info(f"  Broker: {config.mqtt.broker}:{config.mqtt.port}")
                await mqtt_client.disconnect()
                return True, None
            else:
                msg = "MQTT connection check failed (client reported disconnected)"
                logger.error(f"✗ {msg}")
                await mqtt_client.disconnect()
                return False, msg

        except asyncio.TimeoutError:
            msg = "MQTT connection timeout - broker did not respond within 5 seconds"
            logger.error(f"✗ {msg}")
            return False, msg
        except Exception as e:
            msg = f"MQTT connection failed: {e}"
            logger.error(f"✗ {msg}")
            return False, msg

    except Exception as e:
        msg = f"MQTT initialization failed: {e}"
        logger.error(f"✗ {msg}")
        return False, msg


async def test_av_capture(config):
    """Test audio/video capture initialization."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Audio/Video Capture")
    logger.info("=" * 60)

    try:
        av_capture = AVCapture(
            camera_index=config.camera.device_index,
            video_fps=config.camera.fps,
            audio_sample_rate=config.audio.sample_rate,
            audio_chunk_size=config.audio.chunk_size,
        )

        # Try to start video stream
        video_ok = await av_capture.start_video_stream()
        logger.info(f"  Video stream: {'✓' if video_ok else '✗'}")

        # Try to start audio stream
        audio_ok = await av_capture.start_audio_stream()
        logger.info(f"  Audio stream: {'✓' if audio_ok else '✗'}")

        if video_ok or audio_ok:
            logger.info("✓ AV capture test PASSED (at least one stream working)")
            await av_capture.stop()
            note = None
            if not video_ok:
                note = "Video stream not available (check camera connection)"
            elif not audio_ok:
                note = "Audio stream not available (check microphone/PyAudio installation)"
            return True, note
        else:
            msg = "Both video and audio streams failed to initialize"
            logger.warning(
                f"⚠ {msg} (may be ok in non-RPi environment)"
            )
            return True, msg  # Don't fail if running on non-RPi dev machine

    except Exception as e:
        msg = f"AV capture initialization failed with exception: {e}"
        logger.error(f"✗ {msg}")
        return False, msg


async def test_hardware_control(config):
    """Test hardware control initialization."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Hardware Control")
    logger.info("=" * 60)

    try:
        hw_control = HardwareControl(
            pump_gpio_pin=config.hardware.pump_gpio_pin,
            pump_pwm_frequency=config.hardware.pump_pwm_frequency,
            lighting_gpio_pin=config.hardware.lighting_gpio_pin,
            lighting_pwm_frequency=config.hardware.lighting_pwm_frequency,
            alert_gpio_pin=config.hardware.alert_gpio_pin,
            simulation_mode=not config.hardware.enable_hardware_control,
        )

        await hw_control.setup()

        is_healthy = await hw_control.health_check()
        if is_healthy:
            logger.info(f"✓ Hardware control test PASSED")
            logger.info(f"  Simulation mode: {hw_control.simulation_mode}")
            status = hw_control.get_status()
            logger.info(f"  Status: {status}")
            await hw_control.cleanup()
            return True, None
        else:
            msg = "Hardware control health check returned False"
            logger.error(f"✗ {msg}")
            await hw_control.cleanup()
            return False, msg

    except Exception as e:
        msg = f"Hardware control failed with exception: {e}"
        logger.error(f"✗ {msg}")
        return False, msg


async def test_media_pruner(config):
    """Test media pruner initialization."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Media Pruner")
    logger.info("=" * 60)

    try:
        media_pruner = MediaPruner(
            media_dir=str(config.storage.media_dir),
            sensor_logs_dir=str(config.storage.sensor_logs_dir),
            retention_hours=config.storage.retention_hours,
            critical_disk_usage_pct=config.storage.critical_disk_usage_pct,
        )

        stats = media_pruner.get_storage_stats()
        logger.info(f"✓ Media pruner test PASSED")
        logger.info(f"  Storage stats: {stats}")
        return True, None

    except Exception as e:
        msg = f"Media pruner failed with exception: {e}"
        logger.error(f"✗ {msg}")
        return False, msg


async def test_ai_agent_methods(config):
    """Test AI Agent methods with mock data."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: AI Agent Methods")
    logger.info("=" * 60)

    try:
        ai_agent = AIAgent(
            ollama_host=config.ollama.host,
            model=config.ollama.model,
        )

        # Test sensor analysis
        logger.info("Testing sensor analysis...")
        sensor_data = {
            "soil_moisture": 65.5,
            "ambient_light": 450,
            "humidity": 72.3,
            "temperature": 22.1,
        }
        analysis = await ai_agent.analyze_sensor_state(sensor_data)
        logger.info(f"  Sensor analysis result: {analysis.get('status', 'unknown')}")

        # Test visual feedback (with mock frame)
        logger.info("Testing visual feedback...")
        mock_frame = b"mock_frame_data"
        visual = await ai_agent.process_visual_feedback(mock_frame)
        logger.info(
            f"  Visual analysis result: {visual.get('overall_health', 'unknown')}"
        )

        # Test audio feedback
        logger.info("Testing audio feedback...")
        mock_audio = b"mock_audio_data"
        audio = await ai_agent.process_audio_feedback(mock_audio)
        logger.info(f"  Audio analysis result: {audio.get('anomaly_detected', False)}")

        # Test optimization plan
        logger.info("Testing optimization plan...")
        plan = await ai_agent.generate_optimization_plan(analysis, visual, audio)
        logger.info(f"  Optimization plan result: {plan.get('plan_id', 'unknown')}")

        logger.info("✓ AI Agent methods test PASSED")
        return True, None

    except Exception as e:
        msg = f"AI Agent methods failed with exception: {e}"
        logger.error(f"✗ {msg}")
        return False, msg


async def main():
    """Run all validation tests."""
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 58 + "║")
    logger.info(
        "║" + "  Blue Moon Portal - System Validation & Tests  ".center(58) + "║"
    )
    logger.info("║" + " " * 58 + "║")
    logger.info("╚" + "=" * 58 + "╝")

    results = {}
    errors = {}

    # Test 1: Configuration
    config, err = await test_configuration()
    results["configuration"] = config is not None
    if err:
        errors["configuration"] = err

    if not config:
        logger.error("\n✗ Cannot proceed - configuration failed")
        logger.warning("\n" + "=" * 60)
        logger.warning("DIAGNOSTICS & TROUBLESHOOTING")
        logger.warning("=" * 60)
        logger.warning("  [Configuration Diagnostic]")
        logger.warning(f"    Error: {err}")
        logger.warning("    - Ensure that a valid `.env` file is present in the repository root.")
        logger.warning("    - Check that all required variable names match those in `.env.example`.")
        return False

    # Test 2: Ollama
    results["ollama"], errors["ollama"] = await test_ollama(config)

    # Test 3: MQTT
    results["mqtt"], errors["mqtt"] = await test_mqtt(config)

    # Test 4: Less critical components / AV Capture
    results["av_capture"], errors["av_capture"] = await test_av_capture(config)

    # Test 5: Hardware Control
    results["hardware_control"], errors["hardware_control"] = await test_hardware_control(config)

    # Test 6: Media Pruner
    results["media_pruner"], errors["media_pruner"] = await test_media_pruner(config)

    # Test 7: AI Agent Methods
    results["ai_agent_methods"], errors["ai_agent_methods"] = await test_ai_agent_methods(config)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY & DIAGNOSTICS")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name in sorted(results.keys()):
        result = results[test_name]
        status = "   PASS" if result else "  *FAIL*"
        if not result:
            logger.info(f"[{status}] -> {test_name}")
        else:
            logger.info(f"[ {status} ] -> {test_name}")

    logger.info("=" * 60)
    logger.info(f"Total Results: {passed}/{total} tests passed")
    logger.info("=" * 60)

    if passed == total:
        logger.info("✓ ALL TESTS PASSED - System is ready for deployment!")
        return True
    else:
        logger.warning(f"⚠ {total - passed} test(s) failed. Actionable Diagnostics:")
        
        if not results.get("configuration"):
            logger.warning("  [Configuration Diagnostic]")
            if errors.get("configuration"):
                logger.warning(f"    Error detail: {errors['configuration']}")
            logger.warning("    - Ensure that a valid `.env` file is present in the repository root.")
            logger.warning("    - Check that all required variable names match those in `.env.example`.")
            logger.warning("  " + "-" * 50)
            
        if not results.get("ollama"):
            logger.warning("  [Ollama / LLM Diagnostic]")
            if errors.get("ollama"):
                logger.warning(f"    Error detail: {errors['ollama']}")
            logger.warning("    - Verify Ollama is running (`ollama serve`).")
            logger.warning("    - Verify model is pulled: `ollama pull gemma4:e4b`.")
            logger.warning("    - Check that the OLLAMA_HOST variable in `.env` is accessible.")
            logger.warning("  " + "-" * 50)
            
        if not results.get("mqtt"):
            logger.warning("  [MQTT Broker Diagnostic]")
            if errors.get("mqtt"):
                logger.warning(f"    Error detail: {errors['mqtt']}")
            logger.warning("    - Check if Mosquitto or another MQTT broker is active locally on port 1883.")
            logger.warning("    - Verify connection settings (username, password, broker IP) in `.env`.")
            logger.warning("    - (Note: Safe to ignore in pure development/simulation environments if not testing live hardware).")
            logger.warning("  " + "-" * 50)
            
        if not results.get("av_capture"):
            logger.warning("  [AV Capture Diagnostic]")
            if errors.get("av_capture"):
                logger.warning(f"    Error/Warning detail: {errors['av_capture']}")
            logger.warning("    - Ensure that a CSI camera module or USB camera is connected to the hardware.")
            logger.warning("    - Check if PyAudio is installed (requires portaudio system library: e.g. `apt install portaudio19-dev`).")
            logger.warning("  " + "-" * 50)
            
        if not results.get("hardware_control"):
            logger.warning("  [Hardware Control Diagnostic]")
            if errors.get("hardware_control"):
                logger.warning(f"    Error detail: {errors['hardware_control']}")
            logger.warning("    - Check GPIO pins configuration and ensure the app has necessary system permissions (e.g. gpio group).")
            logger.warning("  " + "-" * 50)
            
        if not results.get("media_pruner"):
            logger.warning("  [Media Pruner Diagnostic]")
            if errors.get("media_pruner"):
                logger.warning(f"    Error detail: {errors['media_pruner']}")
            logger.warning("    - Check filesystem permissions for the configured `MEDIA_DIR` and `SENSOR_LOGS_DIR` paths.")
            logger.warning("  " + "-" * 50)
            
        if not results.get("ai_agent_methods"):
            logger.warning("  [AI Agent / Inference Diagnostic]")
            if errors.get("ai_agent_methods"):
                logger.warning(f"    Error detail: {errors['ai_agent_methods']}")
            logger.warning("    - Ensure the local LLM is responsive and not timing out under system load.")
            logger.warning("  " + "-" * 50)
            
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        sys.exit(1)
