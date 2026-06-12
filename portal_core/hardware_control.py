"""
Hardware Control Module

Manages GPIO/I2C control of physical actuators:
- Pump (irrigation)
- Lighting
- Alert system (buzzer/LED)

Supports both direct GPIO control (RPi) and simulated mode for testing.
"""

import asyncio
import logging
from enum import Enum
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import RPi GPIO library (will fail on non-RPi systems)
try:
    import RPi.GPIO as GPIO  # type: ignore

    ENABLE_GPIO = True
except ImportError:
    ENABLE_GPIO = False
    logger.warning("RPi.GPIO not available; running in simulation mode")


class PumpState(str, Enum):
    """Pump control states."""

    OFF = "off"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LightingState(str, Enum):
    """Lighting control states."""

    OFF = "off"
    DIM = "dim"
    NORMAL = "normal"
    FULL = "full"


class HardwareControl:
    """
    Manages hardware actuator control.

    - Pump control via GPIO PWM
    - Lighting control via GPIO PWM
    - Alert/buzzer control via GPIO
    - Supports simulation mode for development
    """

    def __init__(
        self,
        pump_gpio_pin: Optional[int] = None,
        pump_pwm_frequency: int = 1000,
        lighting_gpio_pin: Optional[int] = None,
        lighting_pwm_frequency: int = 1000,
        alert_gpio_pin: Optional[int] = None,
        simulation_mode: bool = False,
    ):
        """
        Initialize Hardware Control.

        Args:
            pump_gpio_pin: GPIO pin for pump control (BCM numbering)
            pump_pwm_frequency: PWM frequency for pump (Hz)
            lighting_gpio_pin: GPIO pin for lighting control
            lighting_pwm_frequency: PWM frequency for lighting (Hz)
            alert_gpio_pin: GPIO pin for alert/buzzer
            simulation_mode: If True, simulate hardware (no actual GPIO)
        """
        self.pump_gpio_pin = pump_gpio_pin
        self.pump_pwm_frequency = pump_pwm_frequency
        self.lighting_gpio_pin = lighting_gpio_pin
        self.lighting_pwm_frequency = lighting_pwm_frequency
        self.alert_gpio_pin = alert_gpio_pin

        # Use simulation mode if GPIO not available or explicitly requested
        self.simulation_mode = simulation_mode or not ENABLE_GPIO

        # State tracking
        self.pump_state = PumpState.OFF
        self.pump_duty_cycle = 0
        self.lighting_state = LightingState.OFF
        self.lighting_duty_cycle = 0

        # PWM objects (if using real GPIO)
        self.pump_pwm = None
        self.lighting_pwm = None

        # Action history for auditing
        self.action_history: list[dict] = []

        logger.info(
            f"Hardware Control initialized: "
            f"pump_pin={pump_gpio_pin}, lighting_pin={lighting_gpio_pin}, "
            f"alert_pin={alert_gpio_pin}, simulation={self.simulation_mode}"
        )

    async def setup(self):
        """Initialize GPIO pins and PWM objects."""
        if self.simulation_mode:
            logger.info("Running in simulation mode (no actual GPIO)")
            return

        try:
            GPIO.setmode(GPIO.BCM)

            # Setup pump control
            if self.pump_gpio_pin:
                GPIO.setup(self.pump_gpio_pin, GPIO.OUT)
                self.pump_pwm = GPIO.PWM(
                    self.pump_gpio_pin, self.pump_pwm_frequency
                )
                self.pump_pwm.start(0)  # Start at 0% duty cycle
                logger.info(f"Pump GPIO setup: pin={self.pump_gpio_pin}")

            # Setup lighting control
            if self.lighting_gpio_pin:
                GPIO.setup(self.lighting_gpio_pin, GPIO.OUT)
                self.lighting_pwm = GPIO.PWM(
                    self.lighting_gpio_pin, self.lighting_pwm_frequency
                )
                self.lighting_pwm.start(0)  # Start at 0% duty cycle
                logger.info(
                    f"Lighting GPIO setup: pin={self.lighting_gpio_pin}"
                )

            # Setup alert pin
            if self.alert_gpio_pin:
                GPIO.setup(self.alert_gpio_pin, GPIO.OUT)
                GPIO.output(self.alert_gpio_pin, GPIO.LOW)
                logger.info(f"Alert GPIO setup: pin={self.alert_gpio_pin}")

        except Exception as e:
            logger.error(f"GPIO setup error: {e}")
            self.simulation_mode = True

    async def cleanup(self):
        """Clean up GPIO resources."""
        if self.simulation_mode or not ENABLE_GPIO:
            return

        try:
            if self.pump_pwm:
                self.pump_pwm.stop()
            if self.lighting_pwm:
                self.lighting_pwm.stop()
            GPIO.cleanup()
            logger.info("GPIO cleanup complete")
        except Exception as e:
            logger.error(f"GPIO cleanup error: {e}")

    async def set_pump(self, state: PumpState) -> bool:
        """
        Control pump state.

        Args:
            state: Desired pump state (OFF, LOW, MEDIUM, HIGH)

        Returns:
            True if successful
        """
        try:
            duty_cycle_map = {
                PumpState.OFF: 0,
                PumpState.LOW: 33,
                PumpState.MEDIUM: 66,
                PumpState.HIGH: 100,
            }

            duty_cycle = duty_cycle_map.get(state, 0)

            self.pump_state = state
            self.pump_duty_cycle = duty_cycle

            if self.simulation_mode:
                logger.info(f"[SIM] Pump: {state.value} (PWM {duty_cycle}%)")
            else:
                if self.pump_pwm:
                    self.pump_pwm.ChangeDutyCycle(duty_cycle)
                    logger.info(f"Pump: {state.value} (PWM {duty_cycle}%)")

            # Log action
            self._log_action("pump", state.value, duty_cycle)
            return True

        except Exception as e:
            logger.error(f"Pump control error: {e}")
            return False

    async def set_lighting(self, state: LightingState) -> bool:
        """
        Control lighting state.

        Args:
            state: Desired lighting state (OFF, DIM, NORMAL, FULL)

        Returns:
            True if successful
        """
        try:
            duty_cycle_map = {
                LightingState.OFF: 0,
                LightingState.DIM: 25,
                LightingState.NORMAL: 75,
                LightingState.FULL: 100,
            }

            duty_cycle = duty_cycle_map.get(state, 0)

            self.lighting_state = state
            self.lighting_duty_cycle = duty_cycle

            if self.simulation_mode:
                logger.info(
                    f"[SIM] Lighting: {state.value} (PWM {duty_cycle}%)"
                )
            else:
                if self.lighting_pwm:
                    self.lighting_pwm.ChangeDutyCycle(duty_cycle)
                    logger.info(f"Lighting: {state.value} (PWM {duty_cycle}%)")

            # Log action
            self._log_action("lighting", state.value, duty_cycle)
            return True

        except Exception as e:
            logger.error(f"Lighting control error: {e}")
            return False

    async def trigger_alert(self, duration_ms: int = 500):
        """
        Trigger alert/buzzer.

        Args:
            duration_ms: Alert duration in milliseconds
        """
        try:
            if self.simulation_mode:
                logger.warning(f"[SIM] ALERT triggered for {duration_ms}ms")
            else:
                if self.alert_gpio_pin:
                    GPIO.output(self.alert_gpio_pin, GPIO.HIGH)
                    await asyncio.sleep(duration_ms / 1000.0)
                    GPIO.output(self.alert_gpio_pin, GPIO.LOW)
                    logger.warning(f"ALERT triggered for {duration_ms}ms")

            self._log_action("alert", "triggered", duration_ms)

        except Exception as e:
            logger.error(f"Alert trigger error: {e}")

    async def enforce_plan(self, plan: dict) -> bool:
        """
        Enforce a crop optimization plan by setting hardware states.

        Args:
            plan: CropOptimizationPlan dict containing pump_action and lighting_action

        Returns:
            True if all actions were successful
        """
        try:
            logger.info(
                f"Enforcing optimization plan: {plan.get('plan_id', 'unknown')}"
            )

            pump_action = plan.get("pump_action")
            lighting_action = plan.get("lighting_action")

            success = True

            # Execute pump action
            if pump_action:
                try:
                    pump_state = PumpState(
                        pump_action.lower()
                        if isinstance(pump_action, str)
                        else pump_action
                    )
                    pump_ok = await self.set_pump(pump_state)
                    success = success and pump_ok
                except (ValueError, AttributeError) as e:
                    logger.error(f"Invalid pump action: {pump_action} ({e})")
                    success = False

            # Execute lighting action
            if lighting_action:
                try:
                    lighting_state = LightingState(
                        lighting_action.lower()
                        if isinstance(lighting_action, str)
                        else lighting_action
                    )
                    lighting_ok = await self.set_lighting(lighting_state)
                    success = success and lighting_ok
                except (ValueError, AttributeError) as e:
                    logger.error(
                        f"Invalid lighting action: {lighting_action} ({e})"
                    )
                    success = False

            # Trigger alert if plan requires human review
            if plan.get("requires_human_review"):
                await self.trigger_alert(duration_ms=1000)

            logger.info(
                f"Plan enforcement {'successful' if success else 'had errors'}"
            )
            return success

        except Exception as e:
            logger.error(f"Plan enforcement error: {e}")
            return False

    def _log_action(self, device: str, action: str, value: int):
        """Log hardware action to history."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "device": device,
            "action": action,
            "value": value,
        }
        self.action_history.append(log_entry)

        # Keep history to last 1000 entries
        if len(self.action_history) > 1000:
            self.action_history.pop(0)

    def get_status(self) -> dict:
        """Get current hardware status."""
        return {
            "pump": {
                "state": self.pump_state.value,
                "duty_cycle_pct": self.pump_duty_cycle,
            },
            "lighting": {
                "state": self.lighting_state.value,
                "duty_cycle_pct": self.lighting_duty_cycle,
            },
            "simulation_mode": self.simulation_mode,
            "timestamp": datetime.now().isoformat(),
        }

    async def health_check(self) -> bool:
        """Check hardware control system health."""
        try:
            if not self.simulation_mode:
                # If real GPIO, check that pins are configured
                return bool(self.pump_gpio_pin or self.lighting_gpio_pin)
            return True
        except Exception as e:
            logger.error(f"Hardware health check error: {e}")
            return False
