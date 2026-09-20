#!/usr/bin/env python3
"""Fail CI if public posture files regress into install/BOM/overclaim text."""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN = [
    (re.compile(r"BLUE_MOON_", re.I), "legacy BLUE_MOON_ env prefix"),
    (re.compile(r"curl\s+-fsSL.*install\.sh"), "curl|bash install path"),
    (re.compile(r"irm\s+https://raw\.githubusercontent\.com.*install\.ps1"), "iex install path"),
    (re.compile(r"New Zealand'?s leader", re.I), "leadership overclaim"),
    (re.compile(r"collaborating with Venture Taranaki", re.I), "unpublished collaboration claim"),
    (re.compile(r"Kotahitanga Investment Fund", re.I), "unpublished funder claim"),
]

SKIP_REL = {
    "scripts/posture_lint.py",
}

ALLOW_NEGATION_FILES = {
    "PUBLIC_POSTURE.md",
    "REALITY.md",
    "README.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "AGENTS.md",
    "CAT_CONGRUENCE.md",
}

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "assets", "telemetry_data"}


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() in {".md", ".py", ".js", ".sh", ".ps1", ".yml", ".yaml"} or path.name in {
            ".env.example"
        }:
            files.append(path)
        elif path.relative_to(ROOT).as_posix() in {"requirements.txt", "package.json"}:
            files.append(path)
    return files


def main() -> int:
    errors: list[str] = []

    reality = (ROOT / "REALITY.md").read_text(encoding="utf-8", errors="replace")
    if "bootstrap" in reality.lower() and "main loop" in reality.lower():
        errors.append("REALITY.md must not describe a public bootstrap → main loop demo")

    getting = (ROOT / "GETTING_STARTED.md").read_text(encoding="utf-8", errors="replace")
    if "pip install" in getting.lower() or "python main.py" in getting.lower():
        errors.append("GETTING_STARTED.md must remain a not-published notice")

    main_py = (ROOT / "main.py").read_text(encoding="utf-8", errors="replace")
    if re.search(r"^(import|from)\s+\S*(mqtt|gpio)", main_py, re.I | re.M):
        errors.append("main.py must remain a posture stub (no MQTT/GPIO imports)")
    if re.search(r"os\.getenv\(\s*[\"']BLUE_MOON_", main_py):
        errors.append("main.py must not read BLUE_MOON_ env vars")

    for path in iter_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel in SKIP_REL:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern, label in FORBIDDEN:
            if not pattern.search(text):
                continue
            if path.name in ALLOW_NEGATION_FILES:
                continue
            errors.append(f"{rel}: forbidden token ({label})")

    if errors:
        print("posture_lint FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("posture_lint OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
