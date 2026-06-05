"""
Configuration Module

Loads and validates all environment variables for Blue Moon Portal.
Uses Pydantic for strict configuration validation and defaults.
"""

import os
from pathlib import Path
from typing import Optional
import logging

from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class OllamaConfig(BaseModel):
    """Ollama LLM configuration."""

    host: str = Field(default="http://localhost:11434", description="Ollama API host")
    model: str = Field(default="gemma4-e4b", description="Model name")

    @validator("host")
    def validate_host(cls, v):
        if not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError("Ollama host must start with http:// or https://")
        return v

    class Config:
        env_prefix = "OLLAMA_"


class MQTTConfig(BaseModel):
    """MQTT broker configuration."""

    broker: str = Field(default="localhost", description="MQTT broker hostname")
    port: int = Field(default=1883, ge=1, le=65535, description="MQTT port")
    username: Optional[str] = Field(default=None, description="MQTT username")
    password: Optional[str] = Field(default=None, description="MQTT password")
    topic_prefix: str = Field(
        default="horowhenua/sensors", description="MQTT topic prefix"
    )

    class Config:
        env_prefix = "MQTT_"


class StorageConfig(BaseModel):
    """Storage and media configuration."""

    media_dir: Path = Field(
        default=Path("./telemetry_data/media"), description="Media storage directory"
    )
    sensor_logs_dir: Path = Field(
        default=Path("./telemetry_data/sensor_logs"),
        description="Sensor logs directory",
    )
    retention_hours: int = Field(
        default=48, ge=1, description="Media retention period in hours"
    )
    critical_disk_usage_pct: float = Field(
        default=85.0, ge=50, le=99, description="Critical disk usage threshold"
    )

    @validator("media_dir", "sensor_logs_dir", pre=True)
    def validate_paths(cls, v):
        path = Path(v) if isinstance(v, str) else v
        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        return path

    class Config:
        env_prefix = ""  # Use exact names


class CameraConfig(BaseModel):
    """Camera/video configuration."""

    device_index: int = Field(default=0, ge=0, description="Camera device index")
    fps: int = Field(default=30, ge=15, le=120, description="Video frame rate")

    class Config:
        env_prefix = "CAMERA_"


class AudioConfig(BaseModel):
    """Audio configuration."""

    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")
    chunk_size: int = Field(
        default=4096, ge=512, le=65536, description="Audio chunk size in samples"
    )

    @validator("sample_rate")
    def validate_sample_rate(cls, v):
        valid_rates = [8000, 16000, 44100, 48000]
        if v not in valid_rates:
            raise ValueError(f"Sample rate must be one of {valid_rates}")
        return v

    class Config:
        env_prefix = "AUDIO_"


class HardwareConfig(BaseModel):
    """Hardware GPIO and control configuration."""

    pump_gpio_pin: Optional[int] = Field(default=None, description="Pump GPIO pin")
    pump_pwm_frequency: int = Field(
        default=1000, ge=100, le=10000, description="Pump PWM frequency"
    )
    lighting_gpio_pin: Optional[int] = Field(
        default=None, description="Lighting GPIO pin"
    )
    lighting_pwm_frequency: int = Field(
        default=1000, ge=100, le=10000, description="Lighting PWM frequency"
    )
    alert_gpio_pin: Optional[int] = Field(default=None, description="Alert GPIO pin")
    enable_hardware_control: bool = Field(
        default=False, description="Enable actual hardware control"
    )

    class Config:
        env_prefix = "HARDWARE_"


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    file: Optional[Path] = Field(default=None, description="Log file path")

    @validator("level")
    def validate_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    class Config:
        env_prefix = ""  # Use exact names


class PortalConfig(BaseModel):
    """Complete Blue Moon Portal configuration."""

    ollama: OllamaConfig
    mqtt: MQTTConfig
    storage: StorageConfig
    camera: CameraConfig
    audio: AudioConfig
    hardware: HardwareConfig
    logging: LoggingConfig

    class Config:
        arbitrary_types_allowed = True


def load_config() -> PortalConfig:
    """
    Load and validate configuration from environment variables.

    Returns:
        PortalConfig object with all validated settings

    Raises:
        ValueError: If configuration is invalid
    """
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"Loaded configuration from {env_file}")
    else:
        logger.warning("No .env file found; using environment variables and defaults")

    try:
        # Parse each configuration section
        ollama_config = OllamaConfig(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "gemma4-e4b"),
        )

        mqtt_config = MQTTConfig(
            broker=os.getenv("MQTT_BROKER", "localhost"),
            port=int(os.getenv("MQTT_PORT", "1883")),
            username=os.getenv("MQTT_USERNAME"),
            password=os.getenv("MQTT_PASSWORD"),
            topic_prefix=os.getenv("MQTT_TOPIC_PREFIX", "horowhenua/sensors"),
        )

        storage_config = StorageConfig(
            media_dir=Path(os.getenv("MEDIA_DIR", "./telemetry_data/media")),
            sensor_logs_dir=Path(
                os.getenv("SENSOR_LOGS_DIR", "./telemetry_data/sensor_logs")
            ),
            retention_hours=int(os.getenv("MEDIA_RETENTION_HOURS", "48")),
            critical_disk_usage_pct=float(os.getenv("CRITICAL_DISK_USAGE_PCT", "85.0")),
        )

        camera_config = CameraConfig(
            device_index=int(os.getenv("CAMERA_DEVICE_INDEX", "0")),
            fps=int(os.getenv("CAMERA_FPS", "30")),
        )

        audio_config = AudioConfig(
            sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
            chunk_size=int(os.getenv("AUDIO_CHUNK_SIZE", "4096")),
        )

        hardware_config = HardwareConfig(
            pump_gpio_pin=(
                int(p) if (p := os.getenv("HARDWARE_PUMP_GPIO_PIN")) else None
            ),
            pump_pwm_frequency=int(os.getenv("HARDWARE_PUMP_PWM_FREQUENCY", "1000")),
            lighting_gpio_pin=(
                int(p) if (p := os.getenv("HARDWARE_LIGHTING_GPIO_PIN")) else None
            ),
            lighting_pwm_frequency=int(
                os.getenv("HARDWARE_LIGHTING_PWM_FREQUENCY", "1000")
            ),
            alert_gpio_pin=(
                int(p) if (p := os.getenv("HARDWARE_ALERT_GPIO_PIN")) else None
            ),
            enable_hardware_control=os.getenv(
                "HARDWARE_ENABLE_HARDWARE_CONTROL", "false"
            ).lower()
            == "true",
        )

        logging_config = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file=Path(f) if (f := os.getenv("LOG_FILE")) else None,
        )

        # Combine into portal config
        config = PortalConfig(
            ollama=ollama_config,
            mqtt=mqtt_config,
            storage=storage_config,
            camera=camera_config,
            audio=audio_config,
            hardware=hardware_config,
            logging=logging_config,
        )

        logger.info("✓ Configuration loaded and validated successfully")
        return config

    except ValueError as e:
        logger.error(f"✗ Configuration validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"✗ Configuration loading error: {e}")
        raise


def print_config(config: PortalConfig):
    """Print current configuration (for debugging)."""
    logger.info("=" * 60)
    logger.info("Blue Moon Portal Configuration")
    logger.info("=" * 60)

    logger.info(f"Ollama Host: {config.ollama.host}")
    logger.info(f"Ollama Model: {config.ollama.model}")

    logger.info(f"MQTT Broker: {config.mqtt.broker}:{config.mqtt.port}")
    logger.info(f"MQTT Topic Prefix: {config.mqtt.topic_prefix}")

    logger.info(f"Media Directory: {config.storage.media_dir}")
    logger.info(f"Sensor Logs Directory: {config.storage.sensor_logs_dir}")
    logger.info(f"Media Retention: {config.storage.retention_hours} hours")

    logger.info(f"Camera Device: {config.camera.device_index}")
    logger.info(f"Camera FPS: {config.camera.fps}")

    logger.info(f"Audio Sample Rate: {config.audio.sample_rate} Hz")
    logger.info(f"Audio Chunk Size: {config.audio.chunk_size}")

    if config.hardware.enable_hardware_control:
        logger.info("Hardware Control: ENABLED")
        logger.info(f"  Pump GPIO: {config.hardware.pump_gpio_pin}")
        logger.info(f"  Lighting GPIO: {config.hardware.lighting_gpio_pin}")
        logger.info(f"  Alert GPIO: {config.hardware.alert_gpio_pin}")
    else:
        logger.info("Hardware Control: DISABLED (simulation mode)")

    logger.info(f"Log Level: {config.logging.level}")

    logger.info("=" * 60)
