#!/usr/bin/env python3
"""Public bootstrap disabled — commercial-track / private."""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "Byte Size Kai: public bootstrap is disabled.\n"
        "Install and bootstrap packs are commercial-track / private.\n"
        "See README.md and PUBLIC_POSTURE.md.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
