# DEVELOPMENT.md – Local Development & Testing

This guide covers setting up a development environment, mocking hardware, and testing strategies for Byte Size Kai.

## Local Development Setup

### Prerequisites

- Python 3.10+ (check with `python3 --version`)
- Git
- A MQTT broker (local Mosquitto or cloud-hosted)
- Optional: Docker (for running Mosquitto locally without system install)

### 1. Clone and Virtual Environment

```bash
# Clone the repository
git clone https://github.com/fivepanelhat/Byte-Size-Kai.git
cd Byte-Size-Kai

# Create virtual environment
python3.10 -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
# or on Windows:
# venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### 2. Install Dependencies

```bash
# Core dependencies
pip install -r requirements.txt

# Development tools (linting, testing, formatting)
pip install -r requirements-dev.txt

# Verify installations
pip list | grep -E "paho|ollama|pydantic|pytest"
```

### 3. Environment Configuration

```bash
# Copy template
cp .env.example .env

# Edit .env for local development
nano .env
```

**Example `.env` for local development:**
```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma4:e4b
MQTT_BROKER=localhost
MQTT_PORT=1883
MEDIA_DIR=./telemetry_data/media
SENSOR_LOGS_DIR=./telemetry_data/sensor_logs
MEDIA_RETENTION_HOURS=48
```

---

## Running Ollama Locally

### Option A: Native Installation

```bash
# macOS (via Homebrew):
brew install ollama
ollama serve

# Linux (see https://ollama.ai/):
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve

# In another terminal:
ollama pull gemma4:e4b
```

### Option B: Docker

```bash
# Run Ollama in Docker (GPU support available)
docker run -d -p 11434:11434 --name ollama ollama/ollama
docker exec ollama ollama pull gemma4:e4b

# For GPU acceleration (NVIDIA):
docker run -d --gpus all -p 11434:11434 --name ollama ollama/ollama
```

**Verify Ollama is running:**
```bash
curl http://localhost:11434/api/tags
# Expected response: {"models": [...]}
```

---

## Running MQTT Broker Locally

### Option A: Mosquitto (Recommended)

```bash
# macOS:
brew install mosquitto
brew services start mosquitto

# Linux:
sudo apt install -y mosquitto
sudo systemctl start mosquitto

# Verify:
mosquitto_pub -h localhost -t "test" -m "hello"
mosquitto_sub -h localhost -t "test"
```

### Option B: Docker

```bash
# Run Mosquitto in Docker
docker run -d -p 1883:1883 -p 9001:9001 --name mosquitto eclipse-mosquitto

# In another terminal, test:
mosquitto_pub -h localhost -t "test" -m "hello"
mosquitto_sub -h localhost -t "test"
```

---

## Mock Sensor Data Generation

For testing without hardware, use the mock MQTT publisher:

### Script: `scripts/mock_mqtt_publisher.py`

```python
#!/usr/bin/env python3
"""
Mock MQTT Publisher - Generates realistic sensor data for testing
"""

import json
import time
import random
from datetime import datetime
import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
CLIENT_ID = "mock-sensor-publisher"

def generate_soil_moisture():
    """Generate realistic soil moisture value (0-100 V scale)"""
    return round(random.uniform(50, 80) + random.gauss(0, 2), 2)

def generate_light_level():
    """Generate realistic light level (lux)"""
    return round(random.uniform(300, 600) + random.gauss(0, 20))

def generate_humidity():
    """Generate realistic relative humidity (%)"""
    return round(random.uniform(60, 80) + random.gauss(0, 3), 1)

def main():
    client = mqtt.Client(client_id=CLIENT_ID)
    client.connect(BROKER_HOST, BROKER_PORT)
    client.loop_start()
    
    print(f"Connected to MQTT broker at {BROKER_HOST}:{BROKER_PORT}")
    
    try:
        while True:
            # Simulate sensor readings
            sensors = [
                {
                    "sensor_id": "soil_moisture_1",
                    "sensor_type": "capacitive_moisture",
                    "value": generate_soil_moisture(),
                    "unit": "V",
                },
                {
                    "sensor_id": "light_1",
                    "sensor_type": "ambient_light",
                    "value": generate_light_level(),
                    "unit": "lux",
                },
                {
                    "sensor_id": "humidity_1",
                    "sensor_type": "humidity",
                    "value": generate_humidity(),
                    "unit": "%RH",
                },
            ]
            
            timestamp = datetime.now().isoformat()
            for sensor in sensors:
                sensor["timestamp"] = timestamp
                topic = f"horowhenua/sensors/{sensor['sensor_id']}"
                payload = json.dumps(sensor)
                client.publish(topic, payload)
                print(f"[{timestamp}] Published to {topic}: {sensor['value']} {sensor['unit']}")
            
            time.sleep(5)  # Publish every 5 seconds
    
    except KeyboardInterrupt:
        print("\nShutting down...")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
```

**Run it:**
```bash
python scripts/mock_mqtt_publisher.py
```

---

## Unit Testing

### Test Structure

```
tests/
├── __init__.py
├── test_ai_agent.py
├── test_mqtt_client.py
├── test_av_capture.py
├── test_media_pruner.py
└── fixtures/
    ├── mock_sensor_data.json
    └── mock_frames.jpg
```

### Example: `tests/test_ai_agent.py`

```python
import pytest
import asyncio
from portal_core.ai_agent import AIAgent
from portal_schemas.ai_models import CropOptimizationPlan

@pytest.fixture
def ai_agent():
    """Fixture: Create AI agent instance"""
    return AIAgent(ollama_host="http://localhost:11434", model="gemma4:e4b")

@pytest.mark.asyncio
async def test_health_check(ai_agent):
    """Test Ollama connectivity"""
    is_healthy = await ai_agent.health_check()
    assert is_healthy, "Ollama should be running and model loaded"

@pytest.mark.asyncio
async def test_analyze_sensor_state(ai_agent):
    """Test sensor analysis"""
    sensor_data = {
        "soil_moisture": 65.3,
        "light_level": 450,
        "humidity": 72,
    }
    result = await ai_agent.analyze_sensor_state(sensor_data)
    assert result is not None
    assert "status" in result

@pytest.mark.asyncio
async def test_generate_optimization_plan(ai_agent):
    """Test plan generation with schema validation"""
    analyses = {
        "sensor_analysis": {"status": "ok"},
        "visual_analysis": {"status": "ok"},
        "audio_analysis": {"status": "ok"},
    }
    plan = await ai_agent.generate_optimization_plan(**analyses)
    
    # Should be parseable as CropOptimizationPlan
    assert "plan_id" in plan or "pump_action" in plan
```

**Run tests:**
```bash
pytest tests/ -v
pytest tests/test_ai_agent.py -v --asyncio-mode=auto

# With coverage:
pytest tests/ --cov=portal_core --cov-report=html
```

### Test Fixtures: `tests/fixtures/mock_sensor_data.json`

```json
{
  "sensor_readings": [
    {
      "sensor_id": "soil_moisture_1",
      "value": 65.3,
      "unit": "V",
      "timestamp": "2026-05-31T23:45:00Z"
    },
    {
      "sensor_id": "light_1",
      "value": 450,
      "unit": "lux",
      "timestamp": "2026-05-31T23:45:00Z"
    },
    {
      "sensor_id": "humidity_1",
      "value": 72.5,
      "unit": "%RH",
      "timestamp": "2026-05-31T23:45:00Z"
    }
  ]
}
```

---

## Integration Testing

### Full End-to-End Mock

Create `tests/test_integration.py` to simulate the full pipeline without hardware:

```python
import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_full_portal_flow():
    """Mock full flow: MQTT → AI → Plan"""
    
    # Mock MQTT message
    mock_sensor_msg = {
        "topic": "horowhenua/sensors/soil_moisture_1",
        "payload": {"value": 65.3, "unit": "V"},
        "timestamp": "2026-05-31T23:45:00Z",
    }
    
    # Mock LLM response (should conform to CropOptimizationPlan schema)
    mock_llm_response = {
        "plan_id": "opt-2026-05-31-001",
        "pump_action": "medium",
        "lighting_action": "normal",
        "confidence_score": 0.87,
        "execution_window_minutes": 30,
        "requires_human_review": False,
    }
    
    # Mock frame data
    mock_frame_data = b"\xFF\xD8\xFF\xE0"  # JPEG header
    
    # Patch external dependencies
    with patch("portal_core.ai_agent.ollama.Client") as mock_ollama:
        with patch("portal_core.mqtt_client.mqtt.Client") as mock_mqtt:
            with patch("portal_core.av_capture.cv2.VideoCapture") as mock_camera:
                
                # Configure mocks
                mock_ollama_instance = AsyncMock()
                mock_ollama.return_value = mock_ollama_instance
                
                # Assert plan was generated
                assert mock_llm_response["pump_action"] == "medium"
                assert mock_llm_response["confidence_score"] > 0.8
```

---

## Code Quality & Linting

### Black (Code Formatter)

```bash
# Format all Python files
black .

# Check formatting without modifying
black . --check
```

### MyPy (Type Checking)

```bash
# Type check all modules
mypy portal_core/
mypy portal_schemas/

# Strict mode (recommended)
mypy portal_core/ --strict
```

### Pylint

```bash
# Lint portal_core
pylint portal_core/

# Generate report
pylint portal_core/ --output-format=html > pylint_report.html
```

### Pre-Commit Hooks

Create `.pre-commit-config.yaml` to run checks before commits:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
  - repo: https://github.com/pylint-dev/pylint
    rev: v2.17.0
    hooks:
      - id: pylint
```

Install and enable:
```bash
pip install pre-commit
pre-commit install
```

---

## Debugging

### Enable Debug Logging

Set `LOGLEVEL=DEBUG` in `.env`:

```bash
export LOGLEVEL=DEBUG
python main.py
```

This enables detailed logs from all modules.

### Interactive Python Shell

```bash
python3 << 'EOF'
from portal_core.ai_agent import AIAgent
import asyncio

async def test():
    agent = AIAgent()
    health = await agent.health_check()
    print(f"Ollama health: {health}")

asyncio.run(test())
EOF
```

### Manual MQTT Testing

```bash
# Subscribe to all sensor topics
mosquitto_sub -h localhost -t "horowhenua/sensors/#" -v

# In another terminal, publish a test message
mosquitto_pub -h localhost -t "horowhenua/sensors/test" -m '{"test":"data"}'
```

---

## Common Development Tasks

### Add a New Sensor Type

1. Add Pydantic model to `portal_schemas/ai_models.py`
2. Update `portal_core/ai_agent.py` to parse the new sensor type
3. Add mock data generator to `scripts/mock_mqtt_publisher.py`
4. Write unit test in `tests/test_ai_agent.py`

### Test Hardware-Specific Code on Development Machine

Use conditional imports and mock classes:

```python
# In av_capture.py:
try:
    import cv2
except ImportError:
    cv2 = None  # Mock for testing on non-RPi machines

class AVCapture:
    async def capture_frame(self):
        if cv2 is None:
            return b"\x00"  # Return dummy bytes instead of crashing
```

### Generate API Documentation

```bash
pip install pdoc
pdoc --html --output-dir docs portal_core portal_schemas
# Generates HTML docs in ./docs/
```

---

## Deployment Checklist (Before Pushing to Hardware)

- [ ] All unit tests pass: `pytest tests/ -v`
- [ ] Type checking passes: `mypy portal_core/ --strict`
- [ ] Code formatted: `black . --check` (or `black .` to auto-fix)
- [ ] No linting errors: `pylint portal_core/` (score >8.0)
- [ ] No hardcoded secrets in code or `.env` (check with `grep -r "password\|token\|key"`)
- [ ] `.gitignore` excludes `.env`, media buffers, `__pycache__`
- [ ] Documentation is current (README, ARCHITECTURE, HARDWARE_SETUP, DEVELOPMENT)
- [ ] Requirements are pinned: `pip freeze > requirements-test.txt` and compare

---

## Continuous Integration (CI/CD) Setup

Example GitHub Actions workflow (`.github/workflows/tests.yml`):

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: pytest tests/ -v --cov=portal_core
    
    - name: Type check
      run: mypy portal_core/ --strict
    
    - name: Format check
      run: black . --check
```

---

**For hardware deployment, see [HARDWARE_SETUP.md](HARDWARE_SETUP.md).**  
**For architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md).**
