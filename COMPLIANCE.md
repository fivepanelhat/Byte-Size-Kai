# COMPLIANCE.md

**Coastal Alpine Tech Limited** | **Product:** Byte Size Kai
Last updated: 19 July 2026

> Super Grok compliance briefing (19 July 2026). This is **alignment evidence**, not a compliance certificate or legal advice.

## Regulatory Mapping

### New Zealand
- Privacy Act 2020 + **IPP 3A** (Privacy Amendment Act 2025) - effective **1 May 2026**  
  Notification required when personal information is collected indirectly.
- Biometric Processing Privacy Code 2025  
  New biometric processing: 3 November 2025  
  Existing biometric processing: 3 August 2026
- Health Information Privacy Code (applies where health / wellbeing data is processed)
- Te Mana Raraunga principles - primary data sovereignty framework

### European Union
- **EU AI Act** - Annex III high-risk obligations enforceable **2 August 2026**
- Relevant high-risk categories:
  - Health decision support
  - Biometrics (remote identification, categorisation, emotion recognition)
  - Critical infrastructure / essential services
- Required: risk management, data governance, technical documentation, human oversight, logging, transparency, post-market monitoring

### International Standards
- **ISO/IEC 42001** - AI Management System (AIMS)  
  Covers AI policy, risk assessment, data governance, human oversight, monitoring, continual improvement
- **SOC 2** - Security, Availability, Confidentiality, Processing Integrity, Privacy  
  Priority for multi-tenant / customer-facing components

### Core Technical Controls (Mandatory)
- Local-first / offline-native processing by default
- Owner-controlled encryption keys
- No silent data exfiltration
- Explicit Human-in-the-Loop (HITL) gates for high-impact and culturally sensitive decisions
- Data residency under New Zealand control

### Scope Notes
- Current systems prioritise offline-native operation and data minimisation.
- Any future multi-tenant or customer-facing features will be assessed against SOC 2 and EU AI Act high-risk requirements before release.

### Limitations
- Not legal advice; not a certification claim.
- Confirm statute application with NZ counsel before commercial shipping claims.
- Agents inform / draft / prepare only; humans advise / sign / file / send / pay.

---

## Product-specific mapping

This guide details how the **Byte Size Kai** pest control and agricultural lighting automation system complies with New Zealand regulations, farm safety laws, and customary data rights.

---

## 1. Health and Safety at Work Act 2015 (HSWA) & Laser Safety

The use of lasers for pest deterrence (such as illuminating crop predators or zapping insects) introduces safety requirements for agricultural operators:

* **AS/NZS IEC 60825.1 Compliance:** Automated laser systems (typically using Class 3B or Class 4 targeting diodes) must be shielded or dynamically disabled to prevent exposure to humans.
* **Fail-Safe Relay Lockout:** Byte Size Kai operates physical GPIO alert and relay controls. If the system watchdog detects human activity (e.g. canopy doors opened or PIR sensor triggered), the hardware control loops immediately open the circuit, shutting down the targeting laser.
* **Warning Signs & Log Records:** HSWA requires farm operators to log active laser operations. The system maintains a continuous local CSV log of all laser activations, target classifications, and duration times.

---

## 2. Hazardous Substances and New Organisms Act 1996 (HSNO)

The HSNO Act controls the management of environmental pests and hazardous substances on NZ soil:
* **Alternative to Chemical Pesticides:** By utilizing automated physical target tracking and selective laser deterrence, the Byte Size Kai reduces chemical runoff and soil contamination on intensive horticultural properties.
* **Beneficial Insect Safety:** In alignment with environmental guidelines, target verification logic filters out protected honeybees and beneficial pollinators, limiting deterrent activations to verified pest species.

---

## 3. Māori Data Sovereignty (Te Mana Raraunga)

* **Physical Land Stewardship (Kaitiakitanga):** Visual coordinates, crop density reports, and pest activity hotspots represent direct indicators of whenua health.
* **Edge-Bound Logging:** To support data sovereignty, the Byte Size Kai service processes raw camera telemetry and audio watchdogs locally on-device. Production logs and crop status audits are retained strictly on local hardware, ensuring iwi managers keep data custody.
