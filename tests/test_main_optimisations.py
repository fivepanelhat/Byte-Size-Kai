"""Unit tests for Byte Size Kai main-loop optimisations (no hardware required)."""

import os
from pathlib import Path

from main import rotate_flywheel_if_needed, _is_stable_status, ByteSizeKaiPortal, BlueMonPortal, BlueMoonPortal


def test_blue_moon_alias():
    assert BlueMoonPortal is ByteSizeKaiPortal
    assert BlueMonPortal is ByteSizeKaiPortal


def test_is_stable_status():
    assert _is_stable_status({"status": "healthy"}) is True
    assert _is_stable_status({"status": "critical"}) is False
    assert _is_stable_status(None) is False
    assert _is_stable_status(RuntimeError("x")) is False


def test_rotate_flywheel_trims_large_file(tmp_path: Path):
    p = tmp_path / "flywheel.jsonl"
    # Write many lines so size exceeds tiny max_bytes
    lines = [f'{{"i": {i}, "payload": "{"x" * 200}"}}' for i in range(100)]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert p.stat().st_size > 500

    rotate_flywheel_if_needed(p, max_bytes=500, keep_lines=10)
    kept = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(kept) == 10
    assert '"i": 99' in kept[-1]
