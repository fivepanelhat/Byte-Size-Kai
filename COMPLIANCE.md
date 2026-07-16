# Byte Size Kai Compliance & Regulatory Framework Guide

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
