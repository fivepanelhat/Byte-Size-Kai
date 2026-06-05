import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from main import BlueMonPortal
from portal_core.config import load_config


@pytest.fixture
def test_config():
    # Load configuration and force simulation/dev defaults
    config = load_config()
    config.hardware.enable_hardware_control = False  # simulation mode
    config.mqtt.broker = "localhost"
    config.ollama.host = "http://localhost:11434"
    return config


@pytest.mark.asyncio
async def test_full_portal_integration_flow(test_config):
    """Test full orchestrator integration loop: MQTT -> AI -> AV Capture -> Planning -> Actuation."""
    portal = BlueMonPortal(test_config)
    portal.is_running = True

    # Mock sensor message payload
    mock_sensor_msg = {
        "topic": "horowhenua/sensors/soil_moisture_1",
        "payload": {
            "sensor_id": "soil_moisture_1",
            "sensor_type": "capacitive_moisture",
            "value": 65.3,
            "unit": "V",
            "timestamp": "2026-06-05T12:00:00Z",
        },
        "timestamp": "2026-06-05T12:00:00Z",
    }

    # Mock LLM analysis results
    mock_sensor_analysis = {
        "status": "healthy",
        "soil_moisture_trend": "stable",
        "ambient_light_level": "optimal",
        "humidity_status": "optimal",
        "observations": "looking good",
    }
    mock_visual_analysis = {"overall_health": "excellent", "anomalies": "none"}
    mock_audio_analysis = {"anomaly_detected": False, "type": "normal"}

    # Mock optimization plan output
    mock_optimization_plan = {
        "plan_id": "opt-integration-test-01",
        "pump_action": "low",
        "lighting_action": "normal",
        "confidence_score": 0.95,
        "execution_window_minutes": 30,
        "requires_human_review": False,
    }

    # Setup async method mocks on subcomponents
    portal.mqtt_client.read_message = AsyncMock()
    portal.mqtt_client.connect = AsyncMock(return_value=True)
    portal.mqtt_client.disconnect = AsyncMock()

    portal.ai_agent.analyze_sensor_state = AsyncMock(return_value=mock_sensor_analysis)
    portal.ai_agent.process_visual_feedback = AsyncMock(
        return_value=mock_visual_analysis
    )
    portal.ai_agent.process_audio_feedback = AsyncMock(return_value=mock_audio_analysis)
    portal.ai_agent.generate_optimization_plan = AsyncMock(
        return_value=mock_optimization_plan
    )
    portal.ai_agent.health_check = AsyncMock(return_value=True)

    portal.av_capture.start_video_stream = AsyncMock(return_value=True)
    portal.av_capture.start_audio_stream = AsyncMock(return_value=True)
    portal.av_capture.capture_frame = AsyncMock(return_value=b"mock_frame_data")
    portal.av_capture.capture_audio_chunk = AsyncMock(return_value=b"mock_audio_data")
    portal.av_capture.stop = AsyncMock()
    portal.av_capture.health_check = AsyncMock(return_value=True)

    portal.hardware_control.setup = AsyncMock()
    portal.hardware_control.enforce_plan = AsyncMock(return_value=True)
    portal.hardware_control.cleanup = AsyncMock()
    portal.hardware_control.health_check = AsyncMock(return_value=True)

    # Configure read_message to return a mock message, then set is_running = False to stop the loop on next iteration
    async def mock_read_and_stop():
        portal.is_running = False
        return mock_sensor_msg

    portal.mqtt_client.read_message.side_effect = mock_read_and_stop

    # Run the processing loop once
    await portal.process_sensor_loop()

    # Assertions to verify that the pipeline executed correctly
    portal.mqtt_client.read_message.assert_called_once()
    portal.ai_agent.analyze_sensor_state.assert_called_once_with(
        sensor_data=mock_sensor_msg["payload"]
    )
    portal.av_capture.capture_frame.assert_called_once()
    portal.av_capture.capture_audio_chunk.assert_called_once()
    portal.ai_agent.process_visual_feedback.assert_called_once_with(
        frame_data=b"mock_frame_data"
    )
    portal.ai_agent.process_audio_feedback.assert_called_once_with(
        audio_data=b"mock_audio_data"
    )

    portal.ai_agent.generate_optimization_plan.assert_called_once_with(
        sensor_analysis=mock_sensor_analysis,
        visual_analysis=mock_visual_analysis,
        audio_analysis=mock_audio_analysis,
    )

    portal.hardware_control.enforce_plan.assert_called_once_with(mock_optimization_plan)
