# HARDWARE_SETUP.md - Raspberry Pi 5 + Hailo-10H NPU Configuration

This guide covers the physical assembly and software configuration for deploying Byte Size Kai on edge hardware.

## Hardware Bill of Materials

| Component | Part Number / Model | Qty | Notes |
|-----------|---------------------|-----|-------|
| **Compute** | Raspberry Pi 5 (16GB) | 1 | Main orchestrator |
| **Acceleration** | Hailo-10H NPU | 1 | PCIe neural processing unit |
| **Storage** | 512GB NVMe + adapter | 1 | For telemetry_data/ |
| **Camera** | CSI Camera v2 / v3 | 1 | Leaf health monitoring |
| **Audio** | USB Microphone | 1 | Anomaly detection (optional) |
| **ESP32** | ESP32-WROOM-32 | 2-4 | Sensor nodes (soil moisture, light, humidity) |
| **Sensors** (ESP32 attached) | Capacitive soil moisture + DHT22 + BH1750 | As needed | Multi-modal telemetry |
| **Power** | 27W USB-C PSU | 1 | For RPi 5 + peripherals |
| **Networking** | Ethernet or Wi-Fi | 1 | Network connectivity to MQTT broker |

---

## Physical Assembly

### 1. Raspberry Pi 5 Preparation

```bash
# On a development machine, prepare the RPi 5 SD card
# Download Raspberry Pi OS Lite (or Desktop if GUI needed)
# Flash to 32GB+ microSD card using Raspberry Pi Imager

# Once booted on RPi 5:
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential python3.10 python3.10-dev python3-pip git
sudo apt install -y libopencv-dev python3-opencv

# Optional: Install audio stack (if using USB microphone)
sudo apt install -y alsa-utils pulseaudio python3-pyaudio
```

### 2. Install NVMe SSD (Recommended for Media Storage)

The RPi 5 has an M.2 socket for NVMe drives:

```bash
# 1. Power off and unplug RPi 5
# 2. Insert NVMe drive into M.2 socket (angled 30, press down until it clicks)
# 3. Power on

# After boot, format and mount:
sudo fdisk -l # Identify the NVMe device (e.g., /dev/nvme0n1)
sudo mkfs.ext4 /dev/nvme0n1p1
sudo mkdir -p /mnt/nvm
sudo mount /dev/nvme0n1p1 /mnt/nvm
sudo chown pi:pi /mnt/nvm

# Add to /etc/fstab for persistent mounting:
sudo nano /etc/fstab
# Add line: /dev/nvme0n1p1 /mnt/nvm ext4 defaults,noatime 0 2
```

### 3. Connect Hailo-10H NPU (Hailo PCIe Accelerator)

**CRITICAL: This section ensures your NPU is properly configured.**

```bash
# 1. Power off RPi 5
# 2. Gently insert Hailo-10H NPU into the PCIe M.2 edge connector
# (Note: This is NOT the NVMe socket; separate connector on RPi 5)
# 3. Power on

# Verify hardware detection:
lspci | grep -i hailo
lsusb | grep -i hailo

# If detected, you'll see output like:
# 0001:00:00.0 Processing accelerators: Hailo Devices Ltd. Device xxxx

# Install Hailo drivers and tools:
wget https://github.com/hailo-ai/hailort/releases/download/v4.18.0/hailort-4.18.0-rpi5.tar.gz
tar -xzf hailort-4.18.0-rpi5.tar.gz
cd hailort-4.18.0
sudo ./install.sh

# Install hailort Python bindings:
pip install --upgrade pip setuptools wheel
pip install hailort

# Verify installation:
python3 -c "import hailort; print(hailort.__version__)"
hailo --help
```

### 4. Connect CSI Camera

```bash
# 1. Power off RPi 5
# 2. Locate CSI camera connector (blue ribbon on RPi 5 board)
# 3. Open the retention clip by pulling straight up
# 4. Insert camera ribbon (blue side facing outward, toward you)
# 5. Push the retention clip down until it clicks

# After boot, enable camera in raspi-config:
sudo raspi-config
# Navigate: Interfacing Options > Camera > Enable
# Reboot

# Verify detection:
vcgencmd get_camera
# Expected output: supported=1 detected=1

# Test with OpenCV:
python3 << 'EOF'
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print(f"Frame captured: {frame.shape if ret else 'FAILED'}")
cap.release()
EOF
```

### 5. Connect Microphone (Optional, for Audio Anomaly Detection)

```bash
# USB microphone: Simply plug into RPi 5 USB port

# I2S microphone (lower latency):
# Requires I2S hat + additional wiring; see Hailo docs for audio module setup

# Verify audio device detection:
arecord -l
# Should list: USB Microphone or I2S device

# Test recording:
arecord -d 3 -f cd -t wav test.wav # Record 3 seconds
aplay test.wav # Playback
```

### 6. ESP32 Sensor Nodes

Configure 2-4 ESP32 microcontrollers as MQTT publishers:

```cpp
// Pseudocode for ESP32 firmware (use Arduino IDE or PlatformIO)

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* ssid = "your_wifi";
const char* password = "your_password";
const char* mqtt_server = "192.168.1.100"; // RPi 5 MQTT broker IP

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
 Serial.begin(115200);
 
 // Connect to WiFi
 WiFi.begin(ssid, password);
 while (WiFi.status() != WL_CONNECTED) delay(500);
 
 // Connect to MQTT
 client.setServer(mqtt_server, 1883);
 while (!client.connected()) {
 if (client.connect("ESP32_Sensor_1")) {
 Serial.println("MQTT Connected");
 } else delay(5000);
 }
}

void loop() {
 // Read soil moisture (ADC pin)
 int raw_soil = analogRead(A0);
 float soil_voltage = (raw_soil / 4095.0) * 3.3;
 
 // Read humidity + temperature (DHT22)
 float humidity = dht.readHumidity();
 float temperature = dht.readTemperature();
 
 // Read ambient light (BH1750)
 uint16_t lux = lightMeter.readLightLevel();
 
 // Publish to MQTT
 StaticJsonDocument<256> doc;
 doc["sensor_id"] = "soil_moisture_1";
 doc["value"] = soil_voltage;
 doc["unit"] = "V";
 doc["timestamp"] = millis();
 
 char buffer[256];
 serializeJson(doc, buffer);
 client.publish("horowhenua/sensors/soil_moisture_1", buffer);
 
 delay(5000); // Publish every 5 seconds
}
```

---

## Ollama Installation (Local LLM Runtime)

```bash
# Download Ollama for ARM64 (RPi 5 runs 64-bit OS)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
sudo systemctl start ollama
sudo systemctl enable ollama # Auto-start on boot

# Download Gemma 4 E4B model (requires ~8-12GB storage)
ollama pull gemma4:e4b

# Verify model is loaded:
ollama list
# Expected output:
# NAME ID SIZE MODIFIED
# gemma4:e4b xyz... 9.5GB 10 minutes ago

# Test the model:
ollama run gemma4:e4b "What is 2+2?"

# Optional: Configure Ollama to use GPU/NPU if available
# Edit /etc/systemd/system/ollama.service
# Add environment variables:
# Environment="OLLAMA_NUM_GPU=1"
# Restart: sudo systemctl restart ollama
```

### Ollama API Configuration

The AIAgent in Byte Size Kai communicates with Ollama via HTTP API:

```python
import ollama

client = ollama.Client(host='http://localhost:11434')

response = client.generate(
 model='gemma4:e4b',
 prompt='Your prompt here',
 stream=False
)
print(response['response'])
```

---

## MQTT Broker Setup

### Option A: Mosquitto (Local Broker on RPi 5)

```bash
# Install Mosquitto
sudo apt install -y mosquitto mosquitto-clients

# Start service
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# Test broker connectivity
mosquitto_sub -h localhost -t "horowhenua/sensors/#"

# In another terminal:
mosquitto_pub -h localhost -t "horowhenua/sensors/test" -m '{"test":"message"}'
```

### Option B: External MQTT Broker

If using a cloud or separate MQTT server, configure `.env`:
```
MQTT_BROKER=mqtt.example.com
MQTT_PORT=1883
MQTT_USERNAME=username
MQTT_PASSWORD=password
```

---

## Environment Configuration

Create `.env` file with your hardware details:

```bash
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma4:e4b

# MQTT Configuration
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# Storage Configuration
MEDIA_DIR=/mnt/nvm/telemetry_data/media
SENSOR_LOGS_DIR=/mnt/nvm/telemetry_data/sensor_logs
MEDIA_RETENTION_HOURS=48

# Optional: CAMERA & AUDIO
CAMERA_DEVICE_INDEX=0
CAMERA_FPS=30
AUDIO_SAMPLE_RATE=16000
AUDIO_CHUNK_SIZE=4096
```

---

## Systemd Service for Auto-Start

Create `/etc/systemd/system/blue-moon.service`:

```ini
[Unit]
Description=Byte Size Kai - Autonomous Crop Tracker
Documentation=https://github.com/fivepanelhat/Byte-Size-Kai
After=network.target ollama.service mosquitto.service
Requires=ollama.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/blue-moon-portal
Environment="PATH=/home/pi/blue-moon-portal/venv/bin"
ExecStart=/home/pi/blue-moon-portal/venv/bin/python main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits (prevent runaway processes)
MemoryMax=4G
CPUQuota=80%

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable blue-moon.service
sudo systemctl start blue-moon.service

# Check status:
sudo systemctl status blue-moon.service
journalctl -u blue-moon.service -f # Follow logs
```

---

## Verification Checklist

Before running the portal, verify all hardware:

- [ ] RPi 5 booted and updated (`sudo apt update && sudo apt upgrade`)
- [ ] NVMe SSD mounted at `/mnt/nvm` (or alt storage configured)
- [ ] Hailo-10H NPU detected (`lspci | grep hailo`)
- [ ] Hailo drivers installed (`hailo --help` works)
- [ ] CSI camera connected and detected (`vcgencmd get_camera` -> supported=1 detected=1)
- [ ] Microphone detected (`arecord -l` shows device)
- [ ] Ollama running (`curl http://localhost:11434/api/tags`)
- [ ] Gemma 4 E4B model downloaded (`ollama list`)
- [ ] MQTT broker running (`mosquitto_pub -h localhost -t test -m hi`)
- [ ] ESP32 nodes connected to broker (check `mosquitto_sub` for sensor topics)
- [ ] Python venv set up and dependencies installed (`pip list | grep paho`)
- [ ] `.env` file configured with correct paths and MQTT details
- [ ] Systemd service file created and enabled

---

## Troubleshooting

### Hailo-10H NPU Not Detected

```bash
# Check PCIe bus:
sudo lspci -v | grep -A5 hailo

# Reseat the module (power off, remove, reinstall firmly)
# Check for bent pins or debris in connector
# Try alternate PCIe slot if available (rarely necessary)
```

### CSI Camera Not Detected

```bash
# Verify ribbon cable is fully inserted and retention clip is engaged
# Check in raspi-config: Interfacing Options > Camera > Enable
sudo reboot

# Manual test with rpicam-hello:
sudo apt install -y libcamera0 rpicam-apps
rpicam-hello -t 5000 # Preview for 5 seconds
```

### Ollama Unresponsive

```bash
# Check service status:
sudo systemctl status ollama

# Restart:
sudo systemctl restart ollama

# Check logs:
journalctl -u ollama -n 50

# Manual restart (if service doesn't work):
ps aux | grep ollama
kill -9 <ollama_pid>
ollama serve # Restart manually
```

### MQTT Broker Not Accepting Connections

```bash
# Check Mosquitto status:
sudo systemctl status mosquitto

# Verify listener configuration:
sudo cat /etc/mosquitto/mosquitto.conf | grep -i listener

# If needed, add to config:
# listener 1883
# protocol mqtt
# address 0.0.0.0

# Restart:
sudo systemctl restart mosquitto
```

### Storage Filling Up Too Quickly

- Check media pruning is running: `sudo systemctl status blue-moon | grep media_pruner`
- Lower `MEDIA_RETENTION_HOURS` (default 48)
- Check disk usage: `df -h /mnt/nvm`
- Manually trigger cleanup: `python3 -c "from portal_core.media_pruner import MediaPruner; m = MediaPruner(); m.prune_old_media()"`

---

## Performance Tuning (Optional)

### GPU Offloading (if using Raspberry Pi GPU)

```bash
# Add to Ollama environment:
export OLLAMA_NUM_THREADS=4
export OLLAMA_NUM_GPU=1 # Enable GPU for inference
systemctl restart ollama
```

### NPU Offloading (Hailo-10H NPU)

The Hailo drivers automatically offload compatible operations. No additional configuration needed after driver installation. Monitor performance:

```bash
# Check NPU utilization:
hailortcli benchmark --device-id=0 --model /path/to/model.tflite
```

### Storage I/O Optimization

```bash
# Use NVMe with noatime to reduce writes:
# In /etc/fstab, add "noatime" to mount options
/dev/nvme0n1p1 /mnt/nvm ext4 defaults,noatime 0 2

# Optional: Enable zstd compression for logs
# Media pruner can use zstd instead of gzip (faster)
```

---

**Next Steps:** See [DEVELOPMENT.md](DEVELOPMENT.md) for local development setup and testing strategies.
