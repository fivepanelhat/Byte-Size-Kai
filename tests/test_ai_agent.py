import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from portal_core.ai_agent import AIAgent


@pytest.fixture
def ai_agent():
    return AIAgent(ollama_host="http://localhost:11434", model="gemma4:latest")


@pytest.mark.asyncio
async def test_health_check_healthy(ai_agent):
    """Test health check when Ollama is online and model is loaded."""
    mock_list_response = {"models": [{"name": "gemma4:latest"}]}

    with patch.object(ai_agent.client, "list", return_value=mock_list_response):
        is_healthy = await ai_agent.health_check()
        assert is_healthy is True


@pytest.mark.asyncio
async def test_health_check_unhealthy_missing_model(ai_agent):
    """Test health check when Ollama is online but model is missing."""
    mock_list_response = {"models": [{"name": "other-model:latest"}]}

    with patch.object(ai_agent.client, "list", return_value=mock_list_response):
        is_healthy = await ai_agent.health_check()
        assert is_healthy is False


@pytest.mark.asyncio
async def test_health_check_timeout(ai_agent):
    """Test health check when Ollama times out."""

    async def mock_timeout_list():
        await asyncio.sleep(10.0)
        return {"models": []}

    with patch.object(ai_agent.client, "list", side_effect=asyncio.TimeoutError):
        is_healthy = await ai_agent.health_check()
        assert is_healthy is False


@pytest.mark.asyncio
async def test_analyze_sensor_state_success(ai_agent):
    """Test successful sensor analysis LLM query and parsing."""
    mock_llm_response = {
        "response": '{"status":"healthy", "soil_moisture_trend":"stable", "ambient_light_level":"optimal", "humidity_status":"optimal", "observations":"looking good"}'
    }

    with patch.object(ai_agent.client, "generate", return_value=mock_llm_response):
        sensor_data = {"soil_moisture": 65.5, "ambient_light": 450, "humidity": 72.3}
        analysis = await ai_agent.analyze_sensor_state(sensor_data)

        assert analysis["status"] == "healthy"
        assert analysis["soil_moisture_trend"] == "stable"
        assert "analysis_id" in analysis
        assert "timestamp" in analysis


@pytest.mark.asyncio
async def test_analyze_sensor_state_malformed_json_fallback(ai_agent):
    """Test sensor analysis fallback when LLM returns invalid JSON."""
    mock_llm_response = {
        "response": "This is a freeform text response instead of JSON."
    }

    with patch.object(ai_agent.client, "generate", return_value=mock_llm_response):
        sensor_data = {"soil_moisture": 65.5}
        analysis = await ai_agent.analyze_sensor_state(sensor_data)

        assert analysis["status"] == "unknown"
        assert "observations" in analysis
        assert "This is a freeform" in analysis["observations"]


@pytest.mark.asyncio
async def test_analyze_sensor_state_timeout(ai_agent):
    """Test sensor analysis fallback on timeout."""
    with patch.object(ai_agent.client, "generate", side_effect=asyncio.TimeoutError):
        analysis = await ai_agent.analyze_sensor_state({"soil_moisture": 65.5})
        assert analysis["status"] == "unknown"
        assert "LLM timeout" in analysis["observations"]


@pytest.mark.asyncio
async def test_process_visual_feedback_success(ai_agent):
    """Test successful visual feedback processing (verifying NameError fix)."""
    mock_llm_response = {
        "response": '{"overall_health":"excellent", "anomalies":"none", "confidence":"high"}'
    }

    with patch.object(ai_agent.client, "generate", return_value=mock_llm_response):
        result = await ai_agent.process_visual_feedback(b"mock_jpeg_bytes")
        assert result["overall_health"] == "excellent"
        assert result["anomalies"] == "none"
        assert result["frame_bytes"] == len(b"mock_jpeg_bytes")


@pytest.mark.asyncio
async def test_process_visual_feedback_malformed_json_fallback(ai_agent):
    """Test visual analysis fallback when LLM returns invalid JSON."""
    mock_llm_response = {"response": "Visual output looks fine but not JSON."}

    with patch.object(ai_agent.client, "generate", return_value=mock_llm_response):
        result = await ai_agent.process_visual_feedback(b"mock_jpeg_bytes")
        assert result["overall_health"] == "pending"
        assert result["analysis"] == "Visual output looks fine but not JSON."


@pytest.mark.asyncio
async def test_process_audio_feedback_success(ai_agent):
    """Test successful audio feedback processing."""
    mock_llm_response = {
        "response": '{"anomaly_detected":true, "type":"pump_failure", "confidence":"high"}'
    }

    with patch.object(ai_agent.client, "generate", return_value=mock_llm_response):
        result = await ai_agent.process_audio_feedback(b"mock_audio_bytes")
        assert result["anomaly_detected"] is True
        assert result["type"] == "pump_failure"


@pytest.mark.asyncio
async def test_generate_optimization_plan_success(ai_agent):
    """Test successful crop optimization plan generation and validation."""
    mock_llm_response = {
        "response": '{"plan_id":"opt-20260605-01", "pump_action":"medium", "lighting_action":"normal", "confidence_score":0.85, "execution_window_minutes":30, "requires_human_review":false}'
    }

    with patch.object(ai_agent.client, "generate", return_value=mock_llm_response):
        sensor_analysis = {"status": "healthy"}
        visual_analysis = {"overall_health": "excellent"}
        audio_analysis = {"anomaly_detected": False}

        plan = await ai_agent.generate_optimization_plan(
            sensor_analysis, visual_analysis, audio_analysis
        )
        assert plan["plan_id"] == "opt-20260605-01"
        assert plan["pump_action"] == "medium"
        assert plan["lighting_action"] == "normal"
        assert plan["confidence_score"] == 0.85


@pytest.mark.asyncio
async def test_generate_optimization_plan_invalid_schema_fallback(ai_agent):
    """Test optimization plan fallback when LLM returns plan violating constraints."""
    mock_llm_response = {
        "response": '{"plan_id":"opt-fail", "pump_action":"super_high", "lighting_action":"off"}'  # super_high is invalid pump action
    }

    with patch.object(ai_agent.client, "generate", return_value=mock_llm_response):
        plan = await ai_agent.generate_optimization_plan({}, {}, {})
        assert "opt-default-" in plan["plan_id"]
        assert plan["pump_action"] == "medium"  # default action
        assert plan["requires_human_review"] is True
