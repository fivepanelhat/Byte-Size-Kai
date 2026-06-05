# Blue Moon Portal - Getting Started & Development Guide

## Quick Start

### 1. Clone & Setup Environment

```bash
cd Blue_Moon_Portal

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Minimum required settings:**
- `OLLAMA_HOST` - Point to your Ollama instance (e.g., http://localhost:11434)
- `OLLAMA_MODEL` - Model name (e.g., gemma4-e4b)
- `MQTT_BROKER` - Your MQTT broker address
- `MQTT_PORT` - Usually 1883

### 3. Install Ollama & Model

**Option A: Local Installation**
```bash
# macOS
brew install ollama
ollama serve

# In another terminal
ollama pull gemma4-e4b
```

**Option B: Docker**
```bash
docker run -d -p 11434:11434 --name ollama ollama/ollama
docker exec ollama ollama pull gemma4-e4b
```

### 4. Start MQTT Broker

**Option A: Docker**
```bash
docker run -d -p 1883:1883 --name mqtt eclipse-mosquitto:latest
```

**Option B: Local Mosquitto**
```bash
# macOS
brew install mosquitto
mosquitto

# Linux
sudo apt-get install mosquitto
mosquitto
```

### 5. Validate System

Run the validation script to check all components:

```bash
python validate.py
```

Expected output:
```
╔════════════════════════════════════════════════════════════╗
║     Blue Moon Portal - System Validation & Tests          ║
╚════════════════════════════════════════════════════════════╝

✓ PASS: configuration
✓ PASS: ollama
✓ PASS: mqtt
✓ PASS: av_capture
✓ PASS: hardware_control
✓ PASS: media_pruner
✓ PASS: ai_agent_methods

Results: 7/7 tests passed
✓ ALL TESTS PASSED - System is ready for deployment!
```

### 6. Start Portal

```bash
python main.py
```

You should see:
```
2026-05-31 23:45:00 - __main__ - INFO - Blue Moon Portal orchestrator initialized
2026-05-31 23:45:00 - portal_core.ai_agent - INFO - Ollama health check: OK
2026-05-31 23:45:00 - __main__ - INFO - Blue Moon Portal is ONLINE and processing
```

## Architecture Overview

### Core Components

1. **AIAgent** (`portal_core/ai_agent.py`)
   - Interfaces with Ollama for LLM reasoning
   - Analyzes sensor data, visual frames, and audio
   - Generates optimization plans
   - Enforces Pydantic schema validation

2. **MQTTClient** (`portal_core/mqtt_client.py`)
   - Async Paho MQTT subscriber
   - Ingests sensor telemetry from ESP32
   - Handles connection retry logic
   - Buffers messages in async queue

3. **AVCapture** (`portal_core/av_capture.py`)
   - OpenCV video capture from CSI camera
   - PyAudio microphone capture
   - Feeds multi-modal input to LLM

4. **HardwareControl** (`portal_core/hardware_control.py`)
   - GPIO/PWM control of pump and lighting
   - Supports both real GPIO (RPi) and simulation mode
   - Tracks action history for auditing

5. **MediaPruner** (`portal_core/media_pruner.py`)
   - Auto-cleanup of old media files
   - Log compression (.gz)
   - Disk usage monitoring

6. **Configuration** (`portal_core/config.py`)
   - Pydantic-based configuration validation
   - Environment variable loading with defaults
   - Type-safe configuration access

## Data Flow

```
Sensors (MQTT)
      ↓
  [MQTT Client] → Queue
      ↓
  [AI Agent Analysis]
      ↓
   + Camera Frame → [Visual Feedback]
   + Microphone  → [Audio Feedback]
      ↓
  [Generate Optimization Plan]
      ↓
  [Pydantic Validation]
      ↓
  [Hardware Control]
  - Pump (PWM)
  - Lighting (PWM)
  - Alerts
      ↓
  [Media Pruner] ← Background task
```

## Development Workflow

### Running in Simulation Mode

For development without actual hardware:

```bash
# In .env, set:
ENABLE_HARDWARE_CONTROL=false

# Pump/lighting actions will be logged but not executed
python main.py
```

### Testing Sensor Data

Send mock MQTT data:

```bash
# Using mosquitto_pub
mosquitto_pub -h localhost -t "horowhenua/sensors/soil" -m '{
  "sensor_id": "soil_moisture_1",
  "value": 65.5,
  "unit": "percent"
}'
```

### Debugging

Enable debug logging:

```bash
# In .env, set:
LOG_LEVEL=DEBUG

# Or modify main.py:
logging.basicConfig(level=logging.DEBUG)
```

Check logs:
```bash
# If LOG_FILE is set
tail -f logs/portal.log

# Or pipe stderr
python main.py 2>&1 | tee debug.log
```

### Testing Individual Components

```python
# Test AI Agent
from portal_core.ai_agent import AIAgent

agent = AIAgent(ollama_host="http://localhost:11434", model="gemma4-e4b")
analysis = asyncio.run(agent.analyze_sensor_state({
    "soil_moisture": 65.5,
    "light": 450
}))
print(analysis)

# Test MQTT Client
from portal_core.mqtt_client import MQTTClient

mqtt = MQTTClient(broker_host="localhost")
asyncio.run(mqtt.connect())

# Test Hardware Control
from portal_core.hardware_control import HardwareControl, PumpState

hw = HardwareControl(simulation_mode=True)
asyncio.run(hw.setup())
asyncio.run(hw.set_pump(PumpState.MEDIUM))
```

## Production Deployment

### On Raspberry Pi 5

#### 1. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip

# Install system dependencies
sudo apt install libatlas-base-dev libjasper-dev libtiff5 libjasper1 libharfbuzz0b libwebp6 libopenjp2-7 libopenmj2-0.so.0
```

#### 2. Install RPi.GPIO

```bash
pip install RPi.GPIO
```

#### 3. Create Systemd Service

Create `/etc/systemd/system/blue-moon-portal.service`:

```ini
[Unit]
Description=Blue Moon Portal - Autonomous Crop Optimization
After=network-online.target mqtt.service ollama.service
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Blue_Moon_Portal
Environment="PATH=/home/pi/Blue_Moon_Portal/venv/bin"
ExecStart=/home/pi/Blue_Moon_Portal/venv/bin/python main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 4. Enable & Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable blue-moon-portal
sudo systemctl start blue-moon-portal

# Check status
sudo systemctl status blue-moon-portal

# View logs
sudo journalctl -u blue-moon-portal -f
```

### GPIO Pin Configuration

Default pins (customize in .env):
- Pump: GPIO 17
- Lighting: GPIO 22
- Alert: GPIO 27

Wiring diagram:
```
RPi 5 GPIO 17 → Relay 1 → Pump
RPi 5 GPIO 22 → PWM Pin → LED/Light Controller
RPi 5 GPIO 27 → Buzzer → Alert
```

## Troubleshooting

### Ollama Connection Failed
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not responding:
# - Verify Ollama service is running
# - Check OLLAMA_HOST in .env matches actual host
# - Try http://127.0.0.1:11434 if localhost fails
```

### MQTT Connection Failed
```bash
# Check if broker is running
mosquitto_sub -h localhost -t "horowhenua/sensors/#" -v

# If connection times out:
# - Verify MQTT broker is running
# - Check firewall allows port 1883
# - Verify MQTT_BROKER and MQTT_PORT in .env
```

### Camera Not Found
```bash
# List available cameras
ls -la /dev/video*

# Try different camera index in .env
CAMERA_DEVICE_INDEX=1

# Test OpenCV directly
python3 -c "import cv2; print(cv2.__version__)"
```

### GPIO Permission Denied
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Logout and login again
# Or use sudo (not recommended)
sudo python main.py
```

## Performance Tuning

### Reduce CPU Usage
```bash
# Lower video FPS
CAMERA_FPS=15

# Reduce AI analysis frequency (manual loop modification)
# Increase sensor timeout
```

### Improve Latency
```bash
# Reduce media chunk sizes
AUDIO_CHUNK_SIZE=2048

# Tune LLM request timeout in ai_agent.py
timeout=10.0  # seconds
```

### Storage Management
```bash
# Reduce media retention
MEDIA_RETENTION_HOURS=24

# Adjust critical disk threshold
CRITICAL_DISK_USAGE_PCT=80
```

## Next Steps

- [ ] Set up real MQTT sensor data from ESP32
- [ ] Configure GPIO pins for actual pump/lighting control
- [ ] Deploy to Raspberry Pi 5
- [ ] Integrate with crop monitoring dashboard
- [ ] Add yield prediction model (Phase 2)
- [ ] Implement email/Slack alerting (Phase 2)

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/yourusername/blue-moon-portal/issues
- Documentation: https://github.com/yourusername/blue-moon-portal/wiki
- Contact: info@coastalalpine.co.nz
