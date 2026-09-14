# Byte Size Kai

[![Privacy](https://img.shields.io/badge/Privacy-Local--first%20%2B%20Privacy%20Act%202020-00247D)](./COMPLIANCE.md)
[![Te Mana Raraunga](https://img.shields.io/badge/Te%20Mana%20Raraunga-In%20accordance-0f766e)](./COMPLIANCE.md)
[![HITL](https://img.shields.io/badge/HITL-Draft%2FPrepare%20only-dc2626)](./COMPLIANCE.md)
[![Security](https://img.shields.io/badge/Security-No%20silent%20exfil%20%2B%20SecOps-dc2626)](./SECURITY.md)

**Coastal Alpine Tech Limited** — pre-seed, New Plymouth, Taranaki, Aotearoa New Zealand.

Part of the [Kiwi Edge AI Stack](https://github.com/fivepanelhat/fivepanelhat).

**Agents inform, draft, prepare, monitor, and remind. Humans advise, sign, file, send, pay, and actuate.**

## Product intent

Byte Size Kai is Coastal Alpine Tech’s agritech product for sovereign, on-farm microgreen and crop intelligence: local-first multi-modal sensing and reasoning on Raspberry Pi–class edge hardware (optional Hailo NPU), with Human-in-the-Loop for high-stakes actuation.

## Field context (claim hygiene)

Horowhenua Mana Kai is **early tests / pilot context only**.

- Early field **tests** (not a production on-site deployment) successfully took telemetry from IoT sensors.
- This repository does **not** claim a live deployment fleet, iwi mandate, or partner programme.
- Site names and MQTT topic prefixes are **local configuration** (public template default: `site/sensors`).

See [`PUBLIC_POSTURE.md`](./PUBLIC_POSTURE.md).

## Quick start

```bash
git clone https://github.com/fivepanelhat/Byte-Size-Kai.git
cd Byte-Size-Kai
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bootstrap.py   # or: python main.py
```

Guides: [`GETTING_STARTED.md`](./GETTING_STARTED.md) · [`DEVELOPMENT.md`](./DEVELOPMENT.md) · [`installation.md`](./installation.md)

## Architecture (public)

Deep proprietary architecture, module APIs, schemas, and runtime tables are **not published** on public GitHub.

See the public stub: [`ARCHITECTURE.md`](./ARCHITECTURE.md) · hardware class posture: [`HARDWARE_SETUP.md`](./HARDWARE_SETUP.md)

## Privacy / security / governance

| Commitment | Statement |
| :--- | :--- |
| **No data sales** | We do not sell personal or customer operational data to third parties for ads or brokerage. |
| **NZ Privacy Act 2020** | Designed in accordance with the Privacy Act 2020 IPPs. |
| **Te Mana Raraunga** | Designed in accordance with Te Mana Raraunga principles where Māori data interests arise. |
| **HITL** | Agents draft/prepare; humans approve high-stakes outcomes. |

Details: [`COMPLIANCE.md`](./COMPLIANCE.md) · [`SECURITY.md`](./SECURITY.md)

## License

Proprietary — Coastal Alpine Tech Limited. See `LICENSE`.

## Attribution

**Built by:** Wayne Roberts, Coastal Alpine Tech Limited  
**Field context:** Horowhenua Mana Kai — early **tests only** (successfully took IoT telemetry; not a claimed on-site deployment)  
**Location:** New Plymouth, Taranaki, Aotearoa New Zealand
