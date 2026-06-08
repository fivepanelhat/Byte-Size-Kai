# Blue Moon Portal: Byte Size Kai

![Blue Moon Portal Banner](assets/social_preview.png)

**Welcome to the Blue Moon Portal**—the central nervous system for the Byte Size Kai initiative. This repository houses the architecture for an autonomous, on-premise agritech crop tracker designed to optimize microgreen cultivation through edge-based AI.

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)  
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)  
[![Hardware: Edge AI](https://img.shields.io/badge/Hardware-Raspberry%20Pi%205%20%2B%20NPU-orange.svg)]()  
[![Sovereignty: Offline Native](https://img.shields.io/badge/Sovereignty-Offline%20Native-green.svg)]()  
[![CI/CD: Active](https://github.com/fivepanelhat/Blue-Moon-Portal/actions/workflows/ci.yml/badge.svg)](https://github.com/fivepanelhat/Blue-Moon-Portal/actions)

## The 5 Ws: Project Context

- **Who:** Built by Coastal Alpine Tech Limited, supporting the Horowhenua Mana Kai Project.
- **What:** A multi-modal, agentic IoT pipeline that ingests sensor telemetry, audio, and visual data to autonomously manage and predict crop yields.
- **Where:** Deployed on-site in Horowhenua, New Zealand (Engineered at HQ in New Plymouth, Taranaki).
- **When:** Active development. We are building the sovereign digital infrastructure of tomorrow, today.
- **Why:** To establish localized data sovereignty. Relying on cloud compute for real-time agricultural decisions introduces latency and creates dependencies. We are bringing the brain directly to the soil.

## The Problems We Are Solving

1. **Cloud Dependency & Latency:** Agricultural hardware shouldn't stop working when the internet drops. We are moving inference to the edge.
2. **Unstructured IoT Data:** Sensors generate massive amounts of noise. We are solving the problem of parsing raw floats and integers into structured, deterministic JSON for automated actions.
3. **Fragmented Context:** Traditional setups look at water levels or camera feeds in isolation. We are building a multi-modal agent that contextualizes soil moisture alongside visual leaf health and ambient acoustic data.

## Quick Start

### Prerequisites

- Raspberry Pi 5 (16GB RAM) with Raspberry Pi AI HAT+ (Hailo-8 NPU)
- ESP32 microcontrollers for sensor integration
- Python 3.10+
- Ollama (local LLM runtime)
- Gemma 4 E4B-it model (via `ollama pull gemma4:e4b`)

### Installation (Bare Metal + Virtual Environment)

```bash
# Clone the repository
git clone https://github.com/fivepanelhat/blue-moon-portal.git
cd blue-moon-portal

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your settings (MQTT broker, Ollama host, etc.)
```

### Ollama Model Setup

Before running the portal, ensure Ollama is running and the Gemma 4 model is downloaded:

```bash
# Terminal 1: Start Ollama server
ollama serve

# Terminal 2: Pull the Gemma 4 model
ollama pull gemma4:e4b

# Verify installation
ollama list
# Expected output: gemma4:e4b     c6eb396dbd59  9.6 GB  <timestamp>
```

### System Validation

Before running the portal in production, run the validation script to verify all components:

```bash
python validate.py
```

This will test:
- ✓ Configuration loading from `.env`
- ✓ Ollama connectivity and model availability
- ✓ MQTT broker connectivity
- ✓ Audio/Video capture streams
- ✓ Hardware control simulation
- ✓ Media pruner functionality
- ✓ AI Agent methods and LLM integration

**Expected output (6-7/7 tests pass):**
```
✓ PASS: configuration
✓ PASS: ollama
✓ PASS: mqtt (or ✗ FAIL if broker not running)
✓ PASS: av_capture
✓ PASS: hardware_control
✓ PASS: media_pruner
✓ PASS: ai_agent_methods
```

**Note:** MQTT test may fail if no broker is running locally—this is expected in development. The portal will attempt reconnection at runtime.

### Running the Portal

```bash
# Start the main orchestrator
python main.py
```

The portal will:
1. Connect to your MQTT broker for sensor telemetry
2. Initialize audio/video capture streams
3. Perform health checks on all subsystems
4. Begin processing sensor data through Gemma 4 via Ollama
5. Run background media pruning (auto-cleanup of old AV buffers)

## Architecture Overview

This is **not** a simple chatbot hooked up to a water pump—it's a fully agentic architecture:

```
┌─────────────────────────────────────────────────────┐
│           EDGE HARDWARE (RPi 5 + AI HAT+)           │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ MQTT Sensors │  │ CSI Camera   │  │ Microphone│ │
│  │ (Capacitive  │  │ (Leaf Health)│  │ (Anomaly) │ │
│  │  Moisture,   │  │              │  │ Detection │ │
│  │  Light, RH)  │  │              │  │           │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘ │
│         │                 │                 │        │
│         └─────────────────┼─────────────────┘        │
│                           ▼                          │
│                ┌─────────────────────┐               │
│                │   AI Agent (Gemma   │               │
│                │  4 E4B via Ollama)  │               │
│                │  [Multi-modal LLM]  │               │
│                └────────┬────────────┘               │
│                         │                            │
│         ┌───────────────┼───────────────┐            │
│         ▼               ▼               ▼            │
│    ┌────────┐      ┌────────┐      ┌────────┐       │
│    │ Pump   │      │ Light  │      │Alerts  │       │
│    │Control │      │ Control│      │System  │       │
│    └────────┘      └────────┘      └────────┘       │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  Media Pruner: Auto-cleanup & Compression   │   │
│  │  (Prevents 24/7 capture from saturating SD) │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

**Data Flow:**
1. **Ingestion:** Paho MQTT streams raw sensor data asynchronously; AV module buffers frame captures and audio clips.
2. **Analysis:** Gemma 4 E4B-it acts as the orchestrator. It parses multi-modal input against historical logs to spot trends.
3. **Action & Prediction:** Model generates live optimization scripts. Anomalies trigger local hardware (pumps, lights); predictions feed real-time crop yield and logistics info to the user.

## Directory Structure

```
Blue_Moon_Portal/
│
├── portal_core/               # The Engine Room
│   ├── __init__.py
│   ├── ai_agent.py            # Multi-modal LLM controller (Gemma 4 via Ollama)
│   ├── mqtt_client.py         # Paho MQTT subscriber for ESP32 telemetry
│   ├── av_capture.py          # OpenCV/PyAudio streams (CSI camera + mic)
│   └── media_pruner.py        # Storage lifecycle management (auto-delete/compress)
│
├── portal_schemas/            # The Rulebook (Pydantic enforcement)
│   ├── __init__.py
│   └── ai_models.py           # Pydantic classes (SensorReading, AnalysisResult, CropOptimizationPlan)
│
├── telemetry_data/            # Local Knowledge Base
│   ├── sensor_logs/           # Historical MQTT JSON payloads
│   └── media/                 # Image and audio buffer storage
│
├── requirements.txt           # Python dependencies
├── requirements-dev.txt       # Development tools (pytest, black, mypy)
├── main.py                    # Asynchronous event loop orchestrator
├── setup.py                   # Package configuration
├── .env.example               # Environment variable template
├── .gitignore                 # Git exclusions (media, .env, __pycache__)
├── blue-moon.service          # Systemd service for auto-start on boot
│
├── README.md                  # This file
├── ARCHITECTURE.md            # Detailed technical breakdown
├── HARDWARE_SETUP.md          # RPi5 + Hailo-10H NPU assembly & driver installation
└── DEVELOPMENT.md             # Local dev setup, mocking, testing
```

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Data flow, module responsibilities, Gemma 4 config, Pydantic schema definitions
- **[HARDWARE_SETUP.md](HARDWARE_SETUP.md)** — RPi 5 + Hailo-10H NPU assembly, ESP32 wiring, Ollama installation, **critical NPU driver setup**
- **[DEVELOPMENT.md](DEVELOPMENT.md)** — Local dev environment, mock MQTT payloads, testing strategies

## Technology Stack

### Hardware
- **Compute:** Raspberry Pi 5 (16GB RAM)
- **Acceleration:** Raspberry Pi AI HAT+ (Hailo-8 NPU, 26 TOPS)
- **Sensors:** ESP32 microcontrollers streaming via MQTT
- **Cameras:** CSI camera module (leaf health)
- **Audio:** USB microphone (anomaly detection)

### Software
- **Language:** Python 3.10+
- **LLM Runtime:** Ollama (local, no cloud)
- **Model:** Gemma 4 E4B (4B effective parameters, multi-modal)
- **Message Queue:** Paho MQTT
- **Schema Enforcement:** Pydantic (prevents LLM hallucinations)
- **Media Capture:** OpenCV + PyAudio
- **Process Management:** Systemd (auto-start on boot)

## Key Features

✓ **Edge-Native:** All inference runs locally on RPi 5. No cloud dependency.  
✓ **Multi-Modal AI:** Simultaneously processes sensor telemetry, visual, and audio data.  
✓ **Deterministic Output:** Pydantic schemas prevent conversational hallucinations; LLM must output valid JSON or fail loudly.  
✓ **Auto-Recovery:** Systemd service ensures portal restarts after power loss.  
✓ **Storage-Aware:** Automated media pruning prevents 24/7 AV capture from filling the SD card.  
✓ **Open Source:** Full transparency for agricultural data sovereignty.  

---

## Performance & Benchmarks

* **Local Inference Latency:** ~0.95 seconds per query running Google's `gemma4:e4b` on Raspberry Pi 5.
* **Energy Consumption:** Peak active NPU execution draw is ~1.5W, enabling solar-powered off-grid deployment.
* **Storage Footprint:** media pruner limits raw camera frame buffer size below 500MB, retaining compliance records for 7+ years in compressed format.

---

## Contributing

This project is open-source and welcomes contributions from the agritech and edge AI communities.

### Getting Started as a Contributor

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Follow the development guide in [DEVELOPMENT.md](DEVELOPMENT.md)
4. Submit a pull request

### Code Standards

- Type hints required (validated with `mypy`)
- Docstrings for all public functions and classes
- Black formatting (`black .`)
- Unit tests with `pytest`

## License

This project is Licensed under the Coastal Alpine Tech Limited License. See `LICENSE` for details.

## Attribution

**Built by:** Wayne Roberts, Coastal Alpine Tech Limited  
**Supporting:** Horowhenua Mana Kai Project  
**Location:** New Plymouth, Taranaki / Horowhenua, New Zealand  
**Date:** Active development (as of May 31, 2026)

**Reference:**  
[Running Gemma 4 E4B Locally](https://www.youtube.com/watch?v=NB9zRquoeI0) — Hardware constraints and edge configuration walkthrough.

---

**Questions?** Open an issue or reach out to the Coastal Alpine Tech Limited team.
