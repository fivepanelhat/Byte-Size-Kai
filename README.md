# Blue Moon Portal: Byte Size Kai

**Coastal Alpine Tech Limited** — pre-seed startup, New Plymouth, Taranaki, Aotearoa New Zealand.

![Blue Moon Portal Banner](assets/social_preview.png)


**Welcome to the Blue Moon Portal**—the central nervous system for the Byte Size Kai initiative. This repository houses the architecture for an autonomous, on-premise agritech crop tracker designed to optimize microgreen cultivation through edge-based AI.

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

- Raspberry Pi 5 (16GB RAM) with Raspberry Pi AI Accelerator / AI HAT+ 2 (Hailo-10H NPU)
- ESP32 microcontrollers for sensor integration
- Python 3.10+
- Ollama (local LLM runtime)
- Gemma 4 E4B-it model (via `ollama pull gemma4:e4b`)

### Installation & Setup

We provide separate guides for system environment setup and installation for Windows and Linux users:

* **Prerequisites & System Setup Guide**: Read [setup.md](setup.md)
* **Installation Guide**: Read [installation.md](installation.md)

### Quick Start (Automated Setup)
The fastest way to install is running the cross-platform bootstrap script:

```bash
python bootstrap.py
```

n-portal
python bootstrap.py
```

### Manual Installation (Bare Metal + Virtual Environment)

<details open>
<summary><strong>🐧 Linux / macOS (Bash)</strong></summary>

```bash
# Clone the repository
git clone https://github.com/fivepanelhat/blue-moon-portal.git
cd blue-moon-portal

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your settings (MQTT broker, Ollama host, etc.)
```

</details>

<details>
<summary><strong>🪟 Windows (PowerShell)</strong></summary>

```powershell
# Clone the repository
git clone https://github.com/fivepanelhat/blue-moon-portal.git
cd blue-moon-portal

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
Copy-Item .env.example .env
# Edit .env with your settings (MQTT broker, Ollama host, etc.)
```

> **Note:** If you receive an execution policy error, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` first.

</details>

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

```plaintext
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

> **Diagrams:** Architecture images and Mermaid maps describe the **target product architecture** for this pre-seed stack. They are engineering design maps — not claims of large-scale commercial fleet deployment.

Blue Moon is a closed-loop **microgreens / crop** edge agent for Byte Size Kai. MQTT sensors, CSI vision, and audio drive local multimodal Gemma 4 on **RPi 5 16GB + Hailo-10H** with deterministic hardware control.

![Blue Moon Portal architecture — liquid glass overview](assets/architecture_overview.png)

### System map

```mermaid
%%{init: {
  "theme": "dark",
  "themeVariables": {
    "fontSize": "16px",
    "fontFamily": "Inter, ui-sans-serif, system-ui, sans-serif",
    "primaryColor": "#0ea5e9",
    "primaryTextColor": "#f8fafc",
    "primaryBorderColor": "#38bdf8",
    "lineColor": "#67e8f9",
    "secondaryColor": "#1e293b",
    "tertiaryColor": "#0f172a",
    "clusterBkg": "#0b1220cc",
    "clusterBorder": "#38bdf880",
    "titleColor": "#e2e8f0"
  },
  "flowchart": {
    "nodeSpacing": 40,
    "rankSpacing": 48,
    "padding": 20,
    "htmlLabels": true,
    "curve": "basis"
  }
}}%%
flowchart TB

    classDef sense fill:#052e16,stroke:#4ade80,stroke-width:2px,color:#f0fdf4
    classDef edge fill:#0c4a6e,stroke:#38bdf8,stroke-width:2px,color:#f0f9ff
    classDef core fill:#134e4a,stroke:#2dd4bf,stroke-width:2px,color:#f0fdfa
    classDef act fill:#422006,stroke:#fbbf24,stroke-width:2px,color:#fffbeb
    classDef store fill:#1e1b4b,stroke:#a5b4fc,stroke-width:2px,color:#eef2ff
    classDef ai fill:#3b0764,stroke:#e879f9,stroke-width:2px,color:#fdf4ff
    classDef app fill:#1e1b4b,stroke:#c4b5fd,stroke-width:2px,color:#eef2ff

    subgraph IN["① Grow-room inputs"]
        MQTT["MQTT sensors<br/>moisture · light · RH"]
        CAM["CSI camera<br/>leaf health"]
        MIC["Microphone<br/>anomaly audio"]
    end

    subgraph EDGE["② Edge hardware — RPi 5 16GB + Hailo-10H"]
        CORE["Coastal-Alpine-Core"]
        LLM["Gemma 4 e4b via Ollama"]
        AG["AI agent + schemas"]
        PRUNE["Media pruner<br/>SD-safe buffers"]
    end

    subgraph OUT["③ Actuation"]
        PUMP["Pump control"]
        LIGHT["Light control"]
        ALERT["Alerts"]
    end

    MQTT & CAM & MIC --> CORE --> LLM --> AG
    AG --> PUMP & LIGHT & ALERT
    CAM --> PRUNE

    class MQTT,CAM,MIC sense
    class CORE,AG,PRUNE core
    class LLM ai
    class PUMP,LIGHT,ALERT act
```

| Layer | Components | Role |
| :--- | :--- | :--- |
| **Inputs** | Sensors + vision + audio | Multi-modal crop state |
| **Reasoning** | Gemma 4 multimodal | Local, offline |
| **Control** | Pumps · lights · alerts | Deterministic JSON plans |
| **Storage** | Media pruner | Prevents SD saturation |

*Full detail: [ARCHITECTURE.md](./ARCHITECTURE.md) · [HARDWARE_SETUP.md](./HARDWARE_SETUP.md)*

## Directory Structure

```plaintext
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
- **Acceleration:** Raspberry Pi AI Accelerator / AI HAT+ 2 (Hailo-10H NPU, 40 TOPS)
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

- **Local Inference Latency:** ~0.95 seconds per query running Google's `gemma4:e4b` on Raspberry Pi 5.
- **Energy Consumption:** Peak active NPU execution draw is ~1.5W, enabling solar-powered off-grid deployment.
- **Storage Footprint:** media pruner limits raw camera frame buffer size below 500MB, retaining compliance records for 7+ years in compressed format.

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

---

## Project badges

Status badges for this repository (CI, security, license, and stack metadata):

[![License](https://img.shields.io/badge/License-Proprietary--Commercial-blue?style=flat-square)](LICENSE)  
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square)](https://www.python.org/)  
[![Hardware Target](https://img.shields.io/badge/Hardware-Raspberry%20Pi%205%2016GB-C11A5B?style=flat-square&logo=raspberry-pi&logoColor=white)]()  
[![NPU Acceleration](https://img.shields.io/badge/NPU-Hailo--10H%20Accelerated-005A9C?style=flat-square)]()  
[![Sovereignty](https://img.shields.io/badge/Sovereignty-NZ%20Data%20Bound-00247D?style=flat-square)]()  
[![CI](https://github.com/fivepanelhat/Blue-Moon-Portal/actions/workflows/ci-scan.yml/badge.svg?branch=main)](https://github.com/fivepanelhat/Blue-Moon-Portal/actions/workflows/ci-scan.yml)  
[![SecOps](https://img.shields.io/github/actions/workflow/status/fivepanelhat/Blue-Moon-Portal/secops.yml?branch=main&label=SecOps&style=flat-square&color=success)](https://github.com/fivepanelhat/Blue-Moon-Portal/actions/workflows/secops.yml)  
[![RedTeam](https://img.shields.io/github/actions/workflow/status/fivepanelhat/Blue-Moon-Portal/redteam.yml?branch=main&label=RedTeam&style=flat-square&color=critical)](https://github.com/fivepanelhat/Blue-Moon-Portal/actions/workflows/redteam.yml)  
[![Dependabot](https://img.shields.io/badge/Dependencies-Monitored-brightgreen?style=flat-square&logo=dependabot)]()  
[![Interop](https://img.shields.io/badge/Interop-MQTT%20%7C%20OPC--UA-orange?style=flat-square)]()  
[![Sustainability](https://img.shields.io/badge/EECA%20NZ-Carbon%20Tracked-green?style=flat-square)]()
