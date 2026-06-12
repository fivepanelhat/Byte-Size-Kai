import pytest
import asyncio
import json
from unittest.mock import MagicMock, patch
from portal_core.mqtt_client import MQTTClient


@pytest.fixture
def mqtt_client():
    return MQTTClient(
        broker_host="localhost",
        broker_port=1883,
        client_id="test-client",
        username="user",
        password="password",
    )


@pytest.mark.asyncio
async def test_mqtt_client_init(mqtt_client):
    """Test initialization settings."""
    assert mqtt_client.broker_host == "localhost"
    assert mqtt_client.broker_port == 1883
    assert mqtt_client.client_id == "test-client"
    assert mqtt_client.connected is False


@pytest.mark.asyncio
async def test_mqtt_connect_success(mqtt_client):
    """Test successful connection sequence."""
    with patch.object(mqtt_client.client, "connect") as mock_connect:
        with patch.object(mqtt_client.client, "loop_start") as mock_loop_start:
            success = await mqtt_client.connect()
            assert success is True
            mock_connect.assert_called_once_with(
                "localhost", 1883, keepalive=60
            )
            mock_loop_start.assert_called_once()


@pytest.mark.asyncio
async def test_mqtt_connect_failure_retry(mqtt_client):
    """Test connection retry logic with backoff."""
    with patch.object(
        mqtt_client.client,
        "connect",
        side_effect=Exception("Connection refused"),
    ) as mock_connect:
        # Patch sleep to speed up test
        with patch("asyncio.sleep", return_value=None) as mock_sleep:
            success = await mqtt_client.connect()
            assert success is False
            assert mock_connect.call_count == 3
            assert mock_sleep.call_count == 2  # 2 retries = 2 sleeps


@pytest.mark.asyncio
async def test_mqtt_disconnect(mqtt_client):
    """Test graceful disconnect."""
    with patch.object(mqtt_client.client, "disconnect") as mock_disconnect:
        with patch.object(mqtt_client.client, "loop_stop") as mock_loop_stop:
            await mqtt_client.disconnect()
            mock_disconnect.assert_called_once()
            mock_loop_stop.assert_called_once()


@pytest.mark.asyncio
async def test_on_connect_callback(mqtt_client):
    """Test that connection callback subscribes to topic wildcard."""
    with patch.object(mqtt_client.client, "subscribe") as mock_subscribe:
        mqtt_client._on_connect(None, None, None, rc=0)
        assert mqtt_client.connected is True
        mock_subscribe.assert_called_once_with("horowhenua/sensors/#")


@pytest.mark.asyncio
async def test_on_connect_callback_failure(mqtt_client):
    """Test connection callback with error code."""
    mqtt_client._on_connect(None, None, None, rc=1)
    assert mqtt_client.connected is False


@pytest.mark.asyncio
async def test_on_disconnect_callback(mqtt_client):
    """Test disconnection callback reset state."""
    mqtt_client.connected = True
    mqtt_client._on_disconnect(None, None, rc=1)
    assert mqtt_client.connected is False


@pytest.mark.asyncio
async def test_on_message_callback(mqtt_client):
    """Test message reception and queuing."""
    mock_msg = MagicMock()
    mock_msg.topic = "horowhenua/sensors/soil_moisture_1"
    payload_dict = {"sensor_id": "soil_moisture_1", "value": 65.3}
    mock_msg.payload = json.dumps(payload_dict).encode("utf-8")

    # Run the callback
    mqtt_client._on_message(None, None, mock_msg)

    # Read from the queue (wait up to 1s)
    try:
        queued_msg = await asyncio.wait_for(
            mqtt_client.read_message(), timeout=1.0
        )
        assert queued_msg["topic"] == "horowhenua/sensors/soil_moisture_1"
        assert queued_msg["payload"] == payload_dict
        assert "timestamp" in queued_msg
    except asyncio.TimeoutError:
        pytest.fail("Message was not queued")


@pytest.mark.asyncio
async def test_on_message_callback_malformed(mqtt_client):
    """Test malformed message does not get queued."""
    mock_msg = MagicMock()
    mock_msg.topic = "horowhenua/sensors/soil_moisture_1"
    mock_msg.payload = b"not a json string"

    mqtt_client._on_message(None, None, mock_msg)
    assert mqtt_client.message_queue.empty() is True


@pytest.mark.asyncio
async def test_health_check(mqtt_client):
    """Test health check returns connection status."""
    mqtt_client.connected = False
    assert await mqtt_client.health_check() is False
    mqtt_client.connected = True
    assert await mqtt_client.health_check() is True
