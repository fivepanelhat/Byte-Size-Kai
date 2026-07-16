import pytest
from unittest.mock import patch
from coastal_alpine_core.portal_core.hardware_control import (
 HardwareController,
 ActionState,
)


@pytest.fixture
def hw_control():
 # Force simulation mode for dev/test environment
 return HardwareController(
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
 assert hw_control.config.pump_gpio_pin == 17
 assert hw_control.config.lighting_gpio_pin == 18
 assert hw_control.config.alert_gpio_pin == 27
 assert hw_control.enable_control is False


@pytest.mark.asyncio
async def test_set_pump_states(hw_control):
 """Test setting pump to various states and mapping duty cycles."""
 # Test HIGH
 success = await hw_control.set_pwm_device("pump", ActionState.HIGH)
 assert success is True
 assert hw_control.states["pump"]["state"] == ActionState.HIGH
 assert hw_control.states["pump"]["duty_cycle"] == 100

 # Test MEDIUM
 await hw_control.set_pwm_device("pump", ActionState.MEDIUM)
 assert hw_control.states["pump"]["duty_cycle"] == 66


@pytest.mark.asyncio
async def test_trigger_alert(hw_control):
 """Test alert buzzer triggering log."""
 await hw_control.trigger_alert(duration_ms=100)


@pytest.mark.asyncio
async def test_enforce_plan_success(hw_control):
 """Test enforcing a crop optimization plan with valid commands."""
 plan = {
 "plan_id": "opt-test-1",
 "pump_action": "low",
 "lighting_action": "low",
 "requires_human_review": False,
 }

 success = await hw_control.enforce_plan(plan)
 assert success is True
 assert hw_control.states["pump"]["state"] == ActionState.LOW
 assert hw_control.states["lighting"]["state"] == ActionState.LOW


@pytest.mark.asyncio
async def test_enforce_plan_invalid_values(hw_control):
 """Test plan enforcement with malformed/invalid pump/light command handles gracefully."""
 plan = {
 "plan_id": "opt-test-invalid",
 "pump_action": "invalid_pump_value",
 "lighting_action": "low",
 }

 success = await hw_control.enforce_plan(plan)
 # The light action succeeds, but pump action throws ValueError internally, resulting in overall False
 assert success is False
 # Lighting should still be set to low
 assert hw_control.states["lighting"]["state"] == ActionState.LOW


@pytest.mark.asyncio
async def test_get_status(hw_control):
 """Test getting hardware status summary."""
 status = hw_control.get_status()
 assert "pump" not in status["states"]
 assert status["enabled"] is False


@pytest.mark.asyncio
async def test_health_check(hw_control):
 """Test health check in simulation mode."""
 assert await hw_control.health_check() is True
