import pytest
import asyncio
from unittest.mock import MagicMock, patch
from portal_core.hardware_control import HardwareControl, PumpState, LightingState


@pytest.fixture
def hw_control():
    # Force simulation mode for dev/test environment
    return HardwareControl(
        pump_gpio_pin=17,
        pump_pwm_frequency=1000,
        lighting_gpio_pin=18,
        lighting_pwm_frequency=1000,
        alert_gpio_pin=27,
        simulation_mode=True,
    )


@pytest.mark.asyncio
async def test_hardware_control_init(hw_control):
    """Test initialization parameters."""
    assert hw_control.pump_gpio_pin == 17
    assert hw_control.lighting_gpio_pin == 18
    assert hw_control.alert_gpio_pin == 27
    assert hw_control.simulation_mode is True
    assert hw_control.pump_state == PumpState.OFF
    assert hw_control.lighting_state == LightingState.OFF


@pytest.mark.asyncio
async def test_set_pump_states(hw_control):
    """Test setting pump to various states and mapping duty cycles."""
    # Test HIGH
    success = await hw_control.set_pump(PumpState.HIGH)
    assert success is True
    assert hw_control.pump_state == PumpState.HIGH
    assert hw_control.pump_duty_cycle == 100
    assert len(hw_control.action_history) == 1

    # Test MEDIUM
    await hw_control.set_pump(PumpState.MEDIUM)
    assert hw_control.pump_duty_cycle == 66

    # Test LOW
    await hw_control.set_pump(PumpState.LOW)
    assert hw_control.pump_duty_cycle == 33

    # Test OFF
    await hw_control.set_pump(PumpState.OFF)
    assert hw_control.pump_duty_cycle == 0


@pytest.mark.asyncio
async def test_set_lighting_states(hw_control):
    """Test setting lighting to various states and mapping duty cycles."""
    # Test FULL
    success = await hw_control.set_lighting(LightingState.FULL)
    assert success is True
    assert hw_control.lighting_state == LightingState.FULL
    assert hw_control.lighting_duty_cycle == 100
    assert len(hw_control.action_history) == 1

    # Test NORMAL
    await hw_control.set_lighting(LightingState.NORMAL)
    assert hw_control.lighting_duty_cycle == 75

    # Test DIM
    await hw_control.set_lighting(LightingState.DIM)
    assert hw_control.lighting_duty_cycle == 25

    # Test OFF
    await hw_control.set_lighting(LightingState.OFF)
    assert hw_control.lighting_duty_cycle == 0


@pytest.mark.asyncio
async def test_trigger_alert(hw_control):
    """Test alert buzzer triggering log."""
    await hw_control.trigger_alert(duration_ms=100)
    assert len(hw_control.action_history) == 1
    assert hw_control.action_history[0]["device"] == "alert"


@pytest.mark.asyncio
async def test_enforce_plan_success(hw_control):
    """Test enforcing a crop optimization plan with valid commands."""
    plan = {
        "plan_id": "opt-test-1",
        "pump_action": "low",
        "lighting_action": "dim",
        "requires_human_review": False,
    }

    success = await hw_control.enforce_plan(plan)
    assert success is True
    assert hw_control.pump_state == PumpState.LOW
    assert hw_control.lighting_state == LightingState.DIM


@pytest.mark.asyncio
async def test_enforce_plan_requires_review(hw_control):
    """Test that plans requiring human review trigger buzzer alert."""
    plan = {
        "plan_id": "opt-test-review",
        "pump_action": "medium",
        "lighting_action": "normal",
        "requires_human_review": True,
    }

    with patch.object(hw_control, "trigger_alert", return_value=None) as mock_alert:
        success = await hw_control.enforce_plan(plan)
        assert success is True
        mock_alert.assert_called_once_with(duration_ms=1000)


@pytest.mark.asyncio
async def test_enforce_plan_invalid_values(hw_control):
    """Test plan enforcement with malformed/invalid pump/light command handles gracefully."""
    plan = {
        "plan_id": "opt-test-invalid",
        "pump_action": "invalid_pump_value",
        "lighting_action": "normal",
    }

    success = await hw_control.enforce_plan(plan)
    # The light action succeeds, but pump action throws ValueError internally, resulting in overall False
    assert success is False
    # Lighting should still be set to normal
    assert hw_control.lighting_state == LightingState.NORMAL
    # Pump should remain at its default or previous state (not changed to invalid)
    assert hw_control.pump_state == PumpState.OFF


@pytest.mark.asyncio
async def test_get_status(hw_control):
    """Test getting hardware status summary."""
    status = hw_control.get_status()
    assert status["pump"]["state"] == "off"
    assert status["lighting"]["state"] == "off"
    assert status["simulation_mode"] is True


@pytest.mark.asyncio
async def test_health_check(hw_control):
    """Test health check in simulation mode."""
    assert await hw_control.health_check() is True
