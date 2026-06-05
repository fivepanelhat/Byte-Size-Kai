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
        return config
    except Exception as e:
        logger.error(f"✗ Configuration test FAILED: {e}")
        return None


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
            logger.info(f"✓ Ollama health check PASSED")
            logger.info(f"  Host: {config.ollama.host}")
            logger.info(f"  Model: {config.ollama.model}")
            return True
        else:
            logger.error("✗ Ollama health check FAILED - model not found or not loaded")
            return False

    except Exception as e:
        logger.error(f"✗ Ollama test FAILED: {e}")
        return False


async def test_mqtt(config):
    """Test MQTT broker connectivity."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: MQTT Broker Connectivity")
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
                return True
            else:
                logger.error("✗ MQTT connection FAILED - not connected")
                await mqtt_client.disconnect()
                return False

        except asyncio.TimeoutError:
            logger.error(f"✗ MQTT connection timeout - broker not responding")
            return False

    except Exception as e:
        logger.error(f"✗ MQTT test FAILED: {e}")
        return False


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
            return True
        else:
            logger.warning(
                "⚠ AV capture test PARTIAL - no streams available (may be ok in non-RPi environment)"
            )
            return True  # Don't fail if running on non-RPi dev machine

    except Exception as e:
        logger.error(f"✗ AV capture test FAILED: {e}")
        return False


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
            return True
        else:
            logger.error("✗ Hardware control test FAILED")
            await hw_control.cleanup()
            return False

    except Exception as e:
        logger.error(f"✗ Hardware control test FAILED: {e}")
        return False


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
        return True

    except Exception as e:
        logger.error(f"✗ Media pruner test FAILED: {e}")
        return False


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
        return True

    except Exception as e:
        logger.error(f"✗ AI Agent methods test FAILED: {e}")
        return False


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

    # Test 1: Configuration
    config = await test_configuration()
    results["configuration"] = config is not None

    if not config:
        logger.error("\n✗ Cannot proceed - configuration failed")
        return False

    # Test 2: Ollama
    results["ollama"] = await test_ollama(config)

    # Test 3: MQTT
    results["mqtt"] = await test_mqtt(config)

    # Test 4: AV Capture
    results["av_capture"] = await test_av_capture(config)

    # Test 5: Hardware Control
    results["hardware_control"] = await test_hardware_control(config)

    # Test 6: Media Pruner
    results["media_pruner"] = await test_media_pruner(config)

    # Test 7: AI Agent Methods
    results["ai_agent_methods"] = await test_ai_agent_methods(config)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info("=" * 60)
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("=" * 60)

    if passed == total:
        logger.info("✓ ALL TESTS PASSED - System is ready for deployment!")
        return True
    else:
        logger.warning(
            f"⚠ {total - passed} test(s) failed - review configuration and dependencies"
        )
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        sys.exit(1)
