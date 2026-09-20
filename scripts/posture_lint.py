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
    (re.compile(r"iwi mandate", re.I), "check surrounding negation; bare claim is forbidden"),
]

# Files that may mention forbidden tokens only as explicit denials.
ALLOW_NEGATION_FILES = {
    "PUBLIC_POSTURE.md",
    "REALITY.md",
    "README.md",
    "scripts/posture_lint.py",
    ".github/workflows/ci.yml",
}

SCAN_GLOBS = [
    "*.md",
    "*.py",
    "*.js",
    "*.sh",
    "*.ps1",
    ".env.example",
    ".github/workflows/*.yml",
]

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "assets", "telemetry_data"}


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if path.suffix.lower() in {".md", ".py", ".js", ".sh", ".ps1", ".yml", ".yaml"} or path.name in {
            ".env.example",
            "REALITY.md",
        }:
            files.append(path)
        elif rel in {"requirements.txt", "package.json"}:
            files.append(path)
    return files


def main() -> int:
    errors: list[str] = []

    reality = (ROOT / "REALITY.md").read_text(encoding="utf-8", errors="replace")
    if "bootstrap" in reality.lower() and "main loop" in reality.lower():
        errors.append("REALITY.md must not describe a public bootstrap → main loop demo")
    if re.search(r"Hailo-10H", reality) and "written agreement" not in reality.lower() and "class" not in reality.lower():
        errors.append("REALITY.md must not publish an exact public BOM without NDA fence")

    getting = (ROOT / "GETTING_STARTED.md").read_text(encoding="utf-8", errors="replace")
    if "pip install" in getting.lower() or "python main.py" in getting.lower():
        errors.append("GETTING_STARTED.md must remain a not-published notice")

    main_py = (ROOT / "main.py").read_text(encoding="utf-8", errors="replace")
    if "mqtt" in main_py.lower() or "gpio" in main_py.lower():
        errors.append("main.py must remain a posture stub (no MQTT/GPIO)")

    for path in iter_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT).as_posix()
        for pattern, label in FORBIDDEN:
            if not pattern.search(text):
                continue
            if path.name in ALLOW_NEGATION_FILES and re.search(
                r"(do not|not|unless|forbid|disabled)", text, re.I
            ):
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
