# Architecture — Byte Size Kai (public posture)

**Claim tier: posture only. Pre-seed.**

Detailed proprietary architecture, module APIs, schemas, orchestration internals, hardware bring-up procedures, and runtime performance tables are **not published** on public GitHub. They remain on the commercial / private track under written agreement.

## Intent (public)

Byte Size Kai is Coastal Alpine Tech’s agritech product intent: **local-first**, multi-modal crop intelligence designed to run on edge hardware (Raspberry Pi–class compute with optional NPU acceleration), with **Human-in-the-Loop** for high-stakes actuation and commercial decisions.

Agents **inform, draft, prepare, monitor, and remind**. Humans **advise, sign, file, send, pay, and actuate**.

## Site configuration

Operational names (MQTT topic prefixes, site IDs, field locations) are **local configuration**, not public defaults.

- Example public template prefix: `site/sensors`
- Configure the real prefix in a local `.env` (never commit real site names or credentials)

## Pilot context

Horowhenua **Mana Kai is pilot context only**. This repository does not claim a completed on-site deployment fleet, iwi mandate, or partner programme.

See [`PUBLIC_POSTURE.md`](./PUBLIC_POSTURE.md).

## Where to read next (public)

| Doc | Purpose |
| :--- | :--- |
| [`PUBLIC_POSTURE.md`](./PUBLIC_POSTURE.md) | Claim hygiene |
| [`SECURITY.md`](./SECURITY.md) | Security posture |
| [`COMPLIANCE.md`](./COMPLIANCE.md) | Privacy / Te Mana Raraunga / HITL |
| [`README.md`](./README.md) | Product entry |

## Commercial track

Full architecture maps, hardware commissioning packs, and runtime runbooks are available under NDA / commercial agreement — not on this public surface.

---

*Coastal Alpine Tech Limited · Pre-seed · Taranaki, Aotearoa New Zealand*
