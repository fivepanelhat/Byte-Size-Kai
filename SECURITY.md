# Security Policy — Byte Size Kai

**Updated:** 22 September 2026  
**Status:** Public posture only. Not a penetration-test report or certification.

## Supported versions

Only the `main` branch of this public repository is supported for security *notices*. Runtime, Core pins, and actuator guards live on the commercial-track / private stack.

## How to report a vulnerability

**Do not open a public issue** for security findings.

1. **Preferred:** [GitHub private vulnerability reporting](https://github.com/fivepanelhat/Byte-Size-Kai/security/advisories/new) on this repository.  
   If that page is missing the report button, enable *Private vulnerability reporting* under repository Settings → Code security (founder HITL).
2. Or email **fivepanelhat@gmail.com** with subject `SECURITY: Byte-Size-Kai`.

Include: affected surface (public docs vs suspected runtime), steps to reproduce if safe, and whether the finding is already public.

We will acknowledge receipt when we see the report. Fix timing depends on severity and whether the finding is in this public stub or the private runtime. Do not expect a fixed SLA on a pre-seed public posture repo.

## Fleet principles (public)

- **No silent exfiltration** of personal or tenant operational data.
- **Local-first** default; third-party AI only with explicit operator configuration and disclosure.
- **HITL** on high-stakes production changes and any actuation path.
- **No data sales** of personal information or customer operational data to third parties.
- Designed in accordance with the **Privacy Act 2020** and **Te Mana Raraunga** principles where Māori data interests arise.

## What this public file does not contain

Dependency CVE floors, Core pin versions, actuator fail-closed methods, and org threat-register tables are **commercial-track / private**. They must not be republished here.

CI on this repository uses least-privilege `permissions: contents: read`.

See [`PUBLIC_POSTURE.md`](./PUBLIC_POSTURE.md) · [`NOTICE.md`](./NOTICE.md) · [`COMPLIANCE.md`](./COMPLIANCE.md) · org [Trust Center](https://github.com/fivepanelhat/fivepanelhat/blob/main/TRUST_CENTER.md).
