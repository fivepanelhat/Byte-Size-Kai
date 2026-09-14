# Byte Size Kai — Getting Started (public posture)

**Updated:** 14 September 2026

Public GitHub is **posture-only**. Deep proprietary design, module maps, dataflow diagrams, field bring-up, and commercial commissioning packs are **not published** here.

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) · [`PUBLIC_POSTURE.md`](./PUBLIC_POSTURE.md) · [`HARDWARE_SETUP.md`](./HARDWARE_SETUP.md) · [`.env.example`](./.env.example)

## Quick start (local)

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set OLLAMA_HOST, OLLAMA_MODEL, MQTT_BROKER, MQTT_PORT in .env
python validate.py
python main.py
```

MQTT topic prefixes and site names are **local configuration** (public template default: `site/sensors`).

## What stays private

- Portal / Core module APIs and schemas
- Runtime orchestration and flywheel internals
- Hardware pin maps and field commissioning
- Skill catalogues and procedure bodies

Horowhenua Mana Kai is **early tests / pilot context only** (IoT telemetry success; not a claimed on-site deployment fleet).

Humans still advise, decide, sign, file, send, pay, and actuate.

## Support

- Issues: https://github.com/fivepanelhat/Byte-Size-Kai/issues
