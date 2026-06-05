"""
MQTT Client Module

Async Paho MQTT subscriber for ESP32 telemetry streams.
Ingests raw sensor payloads (soil moisture, light, humidity) from edge hardware.
"""

import asyncio
import json
import logging
from typing import Callable, Optional
from datetime import datetime

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTClient:
    """
    Asynchronous MQTT subscriber for edge sensor telemetry.

    Subscribes to ESP32 topics and buffers sensor readings for LLM analysis.
    """

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: str = "blue-moon-portal",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize MQTT Client.

        Args:
            broker_host: MQTT broker hostname or IP
            broker_port: MQTT broker port (default 1883)
            client_id: Unique client identifier
            username: Optional MQTT username
            password: Optional MQTT password
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        self.connected = False
        self.message_queue: asyncio.Queue = asyncio.Queue()

        # Set authentication if provided
        if username and password:
            self.client.username_pw_set(username, password)

        # Attach callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        logger.info(
            f"MQTT Client initialized: {broker_host}:{broker_port} (id={client_id}, auth={'enabled' if username else 'disabled'})"
        )

    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            self.connected = True
            logger.info("MQTT broker connected")
            # Subscribe to all sensor topics
            self.client.subscribe("horowhenua/sensors/#")
        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection: {rc}")

    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT message."""
        try:
            payload = json.loads(msg.payload.decode())
            logger.debug(f"MQTT message received: {msg.topic}")
            # Enqueue message for async processing
            asyncio.run_coroutine_threadsafe(
                self.message_queue.put(
                    {
                        "topic": msg.topic,
                        "payload": payload,
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
                asyncio.get_event_loop(),
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse MQTT payload: {e}")

    async def connect(self):
        """Establish connection to MQTT broker (async wrapper with retry logic)."""
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                self.client.connect(self.broker_host, self.broker_port, keepalive=60)
                self.client.loop_start()
                logger.info("MQTT connection initiated")
                return True
            except Exception as e:
                logger.error(
                    f"MQTT connection attempt {attempt + 1}/{max_retries} failed: {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # exponential backoff

        logger.error(f"Failed to connect to MQTT broker after {max_retries} attempts")
        return False

    async def disconnect(self):
        """Gracefully disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT disconnected")

    async def read_message(self) -> dict:
        """
        Read next message from MQTT queue (async).

        Returns:
            Message dict: {topic, payload, timestamp}
        """
        return await self.message_queue.get()

    async def health_check(self) -> bool:
        """
        Verify MQTT broker connectivity.

        Returns:
            True if connected to broker
        """
        return self.connected
