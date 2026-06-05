"""
Blue Moon Portal Core Module

The engine room for the autonomous crop tracking agent.
Orchestrates multi-modal data ingestion, LLM reasoning, and hardware enforcement.
"""

__version__ = "0.1.0"
__author__ = "Coastal Alpine Tech Limited"

from .ai_agent import AIAgent
from .mqtt_client import MQTTClient
from .av_capture import AVCapture
from .media_pruner import MediaPruner
from .hardware_control import HardwareControl
from .config import load_config, print_config, PortalConfig

__all__ = [
    "AIAgent",
    "MQTTClient",
    "AVCapture",
    "MediaPruner",
    "HardwareControl",
    "load_config",
    "print_config",
    "PortalConfig",
]
