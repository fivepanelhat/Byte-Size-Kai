# HARDWARE_SETUP.md — public posture

**Claim tier: posture only. Pre-seed.**

Detailed bills of materials, assembly steps, driver install commands, pin maps, and exact node specifications are **commercial-track**. They are not published on public GitHub.

## Public hardware class

Byte Size Kai targets a **Raspberry Pi 5 (16GB-class) + Hailo-10H NPU** edge node with local LLM runtime (Ollama), local MQTT, and optional camera / sensor nodes.

This page does **not**:

- publish a clone-ready BOM or quantities
- publish step-by-step physical assembly
- publish vendor driver URLs, GPIO maps, or field IP examples
- claim a live deployment fleet

Horowhenua Mana Kai is **pilot context only**. No iwi mandate or partner programme is claimed.

## What stays public

- Product intent and HITL policy: [README.md](./README.md)
- Public posture: [PUBLIC_POSTURE.md](./PUBLIC_POSTURE.md)
- High-level architecture map: [ARCHITECTURE.md](./ARCHITECTURE.md) (design map, not a fleet claim)
- Software install path for developers: [installation.md](./installation.md), `python bootstrap.py`

## What is withheld

Exact storage sizes, sensor SKUs, ESP32 counts, PSU ratings, CSI camera revisions, NPU driver versions, systemd unit internals, and site network examples stay off this surface until the founder publishes them.

## HITL

Agents inform, draft, prepare, monitor, and remind. Physical actuation and commercial decisions stay human-in-the-loop unless an explicit local allow-list is configured on-site.

**Next:** use [GETTING_STARTED.md](./GETTING_STARTED.md) and [DEVELOPMENT.md](./DEVELOPMENT.md) for software development. Request the private hardware pack separately.
