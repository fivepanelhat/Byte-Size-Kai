# ARCHITECTURE.md – Blue Moon Portal Technical Design

This document describes the system architecture, data flow, and design principles of the Blue Moon Portal.

## System Overview

The Blue Moon Portal is a **closed-loop, autonomous edge AI system** for real-time crop optimization. It ingests multi-modal data (sensors, vision, audio), reasons over it using Gemma 4 E4B, and generates deterministic hardware commands.

### Design Principles

1. **Edge-First:** All computation happens locally. No cloud dependency = no latency, no data exposure.
2. **Multi-Modal:** Contextualizes decisions across soil moisture, light, humidity, leaf health, and environmental anomalies.
3. **Deterministic:** Pydantic schema enforcement ensures LLM output is always valid JSON; no hallucinations can break hardware.
4. **Resilient:** Systemd auto-start and automatic recovery from power loss.
5. **Storage-Aware:** Media lifecycle management prevents disk saturation on resource-constrained hardware.

---

## Data Flow Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  MQTT Broker ──┐   CSI Camera ──┐   Microphone ──┐              │
│  (ESP32 data)  │   (Vision)      │   (Audio)      │              │
│                └────┬────────────┴────────┬───────┘              │
│                     │                     │                       │
│              ┌──────▼─────────────────────▼──────┐               │
│              │   Data Normalization & Buffering  │               │
│              │  (Parse JSON, frame queue, PCM)  │               │
│              └──────┬──────────────────────────┬─┘               │
│                     │                          │                  │
└─────────────────────┼──────────────────────────┼──────────────────┘

┌─────────────────────┬──────────────────────────┼──────────────────┐
│                PROCESSING LAYER                │                  │
├──────────────────────────────────────────┬────▼──┐                │
│                                          │       │                │
│  ┌──────────────────────────────────┐   │       ▼                │
│  │    AI Agent (Gemma 4 E4B)        │   │  ┌─────────────────┐   │
│  │                                  │◄──┘  │ Historical Logs │   │
│  │  • Sensor analysis               │      │ & Time Series   │   │
│  │  • Visual feature extraction     │      └─────────────────┘   │
│  │  • Audio anomaly detection       │                            │
│  │  • Trend prediction              │                            │
│  │  • Yield forecasting             │                            │
│  └──────────┬───────────────────────┘                            │
│             │                                                     │
│             ▼                                                     │
│  ┌──────────────────────────────────┐                            │
│  │  Pydantic Schema Validation       │                            │
│  │  (Enforce CropOptimizationPlan)   │                            │
│  │  → If invalid → FAIL loudly       │                            │
│  └──────────┬───────────────────────┘                            │
│             │                                                     │
└─────────────┼────────────────────────────────────────────────────┘

┌─────────────┼────────────────────────────────────────────────────┐
│    ACTION LAYER                                                  │
├─────────────▼────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐          │
│  │ Pump Control │  │Light Control │  │Alert/Logging  │          │
│  │ (GPIO/I2C)   │  │ (PWM GPIO)   │  │(MQTT publish) │          │
│  └──────────────┘  └──────────────┘  └───────────────┘          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │   Media Pruner (Background Task)                         │    │
│  │   • Delete old media (>48hrs)                            │    │
│  │   • Compress old logs (.gz)                              │    │
│  │   • Monitor disk usage (alert if >85%)                   │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## Module Responsibilities

### `portal_core/ai_agent.py` — AI Agent (Gemma 4 E4B)

**Purpose:** Core reasoning engine. Analyzes multi-modal input and generates optimization plans.

**Key Methods:**
- `analyze_sensor_state(sensor_data, historical_context)` — Parse telemetry trends
- `process_visual_feedback(frame_data)` — Extract crop health metrics from camera feed
- `process_audio_feedback(audio_data)` — Detect anomalies (pump failure, pests)
- `generate_optimization_plan(sensor_analysis, visual_analysis, audio_analysis)` — Generate Pydantic-validated action plan
- `health_check()` — Verify Ollama and Gemma 4 E4B are loaded

**Configuration:**
- **Model:** Gemma 4 (via `gemma4:e4b`)
- **Ollama Host:** Environment variable `OLLAMA_HOST` (default: `http://localhost:11434`)
- **Model Identifier:** `OLLAMA_MODEL=gemma4:e4b` in `.env`
- **Streaming:** Async/await pattern for non-blocking LLM calls

---

### `portal_core/mqtt_client.py` — MQTT Subscriber

**Purpose:** Real-time telemetry ingestion from ESP32 sensor nodes.

**Key Methods:**
- `connect()` — Establish broker connection
- `read_message()` — Async read from message queue
- `health_check()` — Verify broker connectivity

**Message Format:**
ESP32 publishes JSON to topics like `horowhenua/sensors/soil_moisture_1`:
```json
{
  "sensor_id": "soil_moisture_1",
  "value": 65.3,
  "unit": "V",
  "timestamp": "2026-05-31T23:45:00Z"
}
```

**Subscribed Topics:**
- `horowhenua/sensors/#` (wildcard: all sensor topics)

---

### `portal_core/av_capture.py` — Audio/Video Capture

**Purpose:** Real-time streaming from CSI camera and USB microphone.

**Key Methods:**
- `start_video_stream()` — Initialize OpenCV camera (30 fps)
- `start_audio_stream()` — Initialize PyAudio (16kHz, mono)
- `capture_frame()` — Get single JPEG frame
- `capture_audio_chunk()` — Get audio buffer (4096 samples)
- `health_check()` — Verify both streams are operational

**Hardware:**
- **Camera:** CSI module (native RPi 5 connector)
- **Audio:** USB microphone or I2S audio module

**Encoding:**
- Video: JPEG (compressed)
- Audio: PCM (raw bytes → converted to WAV/FLAC by LLM interface)

---

### `portal_core/media_pruner.py` — Storage Lifecycle Management

**Purpose:** Prevent 24/7 AV capture from saturating RPi 5's SD/NVMe storage.

**Key Methods:**
- `prune_old_media()` — Delete media files >N hours old (default 48hrs)
- `compress_old_logs()` — gzip sensor logs >7 days old
- `check_disk_usage()` — Monitor; alert if >85% full
- `get_storage_stats()` — Return current disk utilization

**Configuration:**
- Retention: `MEDIA_RETENTION_HOURS` env var (default 48)
- Critical threshold: `CRITICAL_DISK_USAGE_PCT` (default 85%)
- Runs on 1-hour cycle in background

**Behavior:**
```
Media File Lifecycle:
1. Captured → stored in telemetry_data/media/
2. Analyzed by LLM → flagged for deletion
3. After 48 hours → auto-deleted
4. If disk >85% → aggressive pruning + alert

Sensor Logs Lifecycle:
1. Accumulated in telemetry_data/sensor_logs/
2. After 7 days → compressed to .gz
3. Archived .gz kept indefinitely (optional S3 backup)
```

---

### `portal_schemas/ai_models.py` — Pydantic Schema Enforcement

**Purpose:** Ensure LLM output conforms to deterministic structures. Prevents hallucinations from breaking hardware.

**Key Classes:**

#### `SensorReading`
```python
SensorReading(
    sensor_id: str,
    sensor_type: str,
    value: float,
    unit: str,
    timestamp: datetime
)
```

#### `AnalysisResult`
```python
AnalysisResult(
    analysis_id: str,
    status: str,  # "healthy", "warning", "critical"
    soil_moisture_trend: str,  # "stable", "increasing", "decreasing"
    ambient_light_level: str,  # "low", "optimal", "high"
    humidity_status: str,
    visual_observations: Optional[str],  # From camera
    audio_observations: Optional[str],   # From microphone
)
```

#### `CropOptimizationPlan` (PRIMARY OUTPUT)
```python
CropOptimizationPlan(
    plan_id: str,
    pump_action: PumpAction,  # "off", "low", "medium", "high"
    lighting_action: LightingAction,  # "off", "dim", "normal", "full"
    predicted_yield_impact: Optional[str],
    logistical_notes: Optional[str],
    confidence_score: float,  # 0.0 - 1.0
    execution_window_minutes: int,
    requires_human_review: bool
)
```

**Validation Flow:**
1. LLM generates JSON response
2. Pydantic validates against schema
3. If invalid → exception → no hardware action
4. If valid → hardware commands enforced atomically

---

## Orchestration Flow (`main.py`)

```python
async def main():
    portal = BlueMonPortal()
    
    # Initialize all components
    ai_agent = AIAgent(ollama_host, model)
    mqtt_client = MQTTClient(broker_host)
    av_capture = AVCapture()
    media_pruner = MediaPruner()
    
    # Health check all subsystems
    health = await portal.health_check()
    
    # Start background tasks
    asyncio.create_task(media_pruner.start())  # Disk cleanup
    asyncio.create_task(sensor_processing_loop())  # Main loop
    
    # Main event loop processes MQTT → LLM → Hardware
    while running:
        message = await mqtt_client.read_message()
        analysis = await ai_agent.analyze_sensor_state(message)
        frame = await av_capture.capture_frame()
        audio = await av_capture.capture_audio_chunk()
        plan = await ai_agent.generate_optimization_plan(...)
        # Execute plan (pump, lights, etc.)
```

---

## Gemma 4 E4B Configuration

### Model Selection

**Gemma 4 E4B** is chosen because:
- ✓ **Effective 4B params** — Fits in RPi 5 RAM with headroom
- ✓ **Multi-modal** — Native support for text, image, audio embeddings
- ✓ **Quantized** — Deployable on edge (typically 4-bit or 8-bit)
- ✓ **Fast inference** — ~100-200ms per token on RPi 5 CPU; faster with Hailo-10H NPU acceleration
- ✓ **Low latency** — Suitable for real-time decision-making in agriculture

### Ollama Setup

Ollama handles model downloading, quantization, and serving:

```bash
# Terminal 1: Start Ollama server
ollama serve

# Terminal 2: Pull the Gemma 4 model
ollama pull gemma4:e4b

# Verify installation
ollama list
# Expected output: gemma4:e4b  c6eb396dbd59  9.6 GB  <timestamp>

# API endpoint (used by AIAgent):
# POST http://localhost:11434/api/generate
```

**Model Information:**
- **Name:** `gemma4:e4b`
- **Size:** ~9.6 GB (GGUF quantized format)
- **Effective Parameters:** 4B (4 billion)
- **Quantization:** Optimized for RPi 5 with Hailo-10H NPU acceleration

### Prompt Engineering

The LLM receives structured prompts:

```
You are an autonomous crop optimization agent. 
You have access to:
- Soil moisture: 65% (stable trend)
- Ambient light: 450 lux (optimal)
- Humidity: 72% (high)
- Visual: Leaf color is healthy green
- Audio: No anomalies detected

Respond with a JSON optimization plan conforming to this schema:
{
  "plan_id": "...",
  "pump_action": "off" | "low" | "medium" | "high",
  "lighting_action": "off" | "dim" | "normal" | "full",
  ...
}

Do not deviate from this schema. Invalid JSON will cause hardware failure.
```

### NPU Acceleration (Hailo-10H NPU)

The Hailo-10H NPU PCIe accelerator offloads neural inference:
- **Without NPU:** Gemma 4 runs on RPi 5 CPU (~5 FPS for video, ~500ms per token)
- **With NPU:** Video processing at 30 FPS, LLM inference 3-5x faster

See [HARDWARE_SETUP.md](HARDWARE_SETUP.md) for driver installation.

---

## System Validation & Readiness

### Validation Script

The `validate.py` script performs comprehensive system checks before production deployment:

```bash
python validate.py
```

**Tests Performed:**

1. **Configuration Test**
   - Loads `.env` file
   - Validates all required environment variables
   - Reports configuration summary

2. **Ollama Health Check**
   - Connects to Ollama API endpoint
   - Verifies Gemma 4 model is loaded and accessible
   - Confirms model version and availability

3. **MQTT Connectivity**
   - Attempts connection to configured MQTT broker
   - Validates message subscription
   - Note: May fail if broker not running locally (expected in dev)

4. **Audio/Video Capture**
   - Tests camera stream initialization
   - Tests microphone/audio stream initialization
   - Expected to warn on non-RPi environments (e.g., development machines)

5. **Hardware Control**
   - Validates GPIO simulation (runs in safe mode on dev machines)
   - Confirms pump and lighting control modules are functional

6. **Media Pruner**
   - Verifies storage directory structure
   - Confirms pruning daemon can initialize
   - Reports current disk usage statistics

7. **AI Agent Methods**
   - Initializes AIAgent with configured Ollama parameters
   - Attempts LLM calls (sensor analysis, visual analysis, audio analysis, optimization planning)
   - Validates Pydantic schema enforcement

**Success Criteria:**
- All tests should pass (6/7 minimum; 7/7 ideal)
- Configuration, Ollama, AV, Hardware, Media, and AI Agent tests **must** pass
- MQTT test may fail if broker not running (acceptable in development)

**Example Output:**
```
✓ PASS: configuration
✓ PASS: ollama
✗ FAIL: mqtt (broker not running - expected in dev)
✓ PASS: av_capture
✓ PASS: hardware_control
✓ PASS: media_pruner
✓ PASS: ai_agent_methods

Results: 6/7 tests passed
⚠ 1 test(s) failed - review configuration and dependencies
```

### Pre-Deployment Checklist

Before deploying the portal to production:

- [ ] Ollama server is running (`ollama serve`)
- [ ] Gemma 4 model is downloaded (`ollama pull gemma4:e4b`)
- [ ] `.env` file is configured with correct MQTT broker, Ollama host, media directories
- [ ] `validate.py` returns 6-7/7 tests passing
- [ ] MQTT broker is accessible (run `validate.py` again if initially failed)
- [ ] CSI camera and USB microphone are physically connected (for RPi deployment)
- [ ] Storage (SD card or NVMe) has >5GB free space
- [ ] Systemd service (`blue-moon.service`) is installed and enabled

---


### Component Failures

| Component | Failure Mode | Recovery |
|-----------|--------------|----------|
| MQTT Broker | Disconnection | Exponential backoff; retry on reconnect |
| Ollama | Offline | Skip LLM step; revert to last-known safe plan |
| Camera | Hardware error | Continue with sensor-only mode |
| Microphone | Hardware error | Continue with sensor+vision mode |
| Disk Full | Storage exceeded | Media pruner triggers aggressive cleanup |

### Systemd Service (Auto-Recovery)

The `blue-moon.service` ensures portal restarts after boot:
```ini
[Unit]
Description=Blue Moon Portal - Autonomous Crop Tracker
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/pi/blue-moon-portal
ExecStart=/home/pi/blue-moon-portal/venv/bin/python main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Performance Characteristics

| Metric | Target | Notes |
|--------|--------|-------|
| **MQTT Latency** | <100ms | Local network; Paho async |
| **Vision Processing** | 30 FPS | CSI camera; OpenCV native |
| **Audio Capture** | 16kHz stereo | USB microphone |
| **LLM Inference** | 200-500ms / token | CPU: ~500ms; with NPU: ~100-150ms |
| **Plan Generation** | <5 seconds | Full multi-modal analysis + LLM call |
| **Media Pruning Cycle** | 1 hour | Background task; low overhead |
| **Disk Footprint** | ~10-50GB / month | Depends on media retention + compression |

---

## Security Considerations

1. **No Internet Required:** All processing is local; no cloud exposure of sensor data.
2. **Pydantic Validation:** Prevents injection attacks via LLM output manipulation.
3. **MQTT Auth:** Configure broker authentication to restrict sensor publishers.
4. **Systemd Isolation:** Service runs as non-root user with minimal privileges.
5. **Future:** Encrypted storage for sensor logs; audit trails for hardware commands.

---

## Future Enhancements (Phase 2+)

- [ ] RAG (Retrieval-Augmented Generation) for long-term learning from historical logs
- [ ] Multi-crop templates (lettuce, spinach, basil, etc.) with adaptive parameters
- [ ] Federated learning across multiple Blue Moon Portals
- [ ] S3/NAS backup for compressed historical data
- [ ] Web dashboard for real-time monitoring
- [ ] Hardware failover (standby RPi 5 for redundancy)

---

**For detailed hardware setup, see [HARDWARE_SETUP.md](HARDWARE_SETUP.md).**  
**For development & testing, see [DEVELOPMENT.md](DEVELOPMENT.md).**
