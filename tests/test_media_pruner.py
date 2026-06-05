import pytest
import asyncio
import gzip
import shutil
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from portal_core.media_pruner import MediaPruner


@pytest.fixture
def temp_dirs(tmp_path):
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    logs_dir = tmp_path / "sensor_logs"
    logs_dir.mkdir()
    return media_dir, logs_dir


@pytest.fixture
def media_pruner(temp_dirs):
    media_dir, logs_dir = temp_dirs
    return MediaPruner(
        media_dir=str(media_dir),
        sensor_logs_dir=str(logs_dir),
        retention_hours=48,
        critical_disk_usage_pct=85.0,
    )


@pytest.mark.asyncio
async def test_prune_old_media(media_pruner, temp_dirs):
    """Test deletion of media files older than retention hours."""
    media_dir, _ = temp_dirs

    # 1. Create a new file (modified now)
    new_file = media_dir / "new_video.jpg"
    new_file.write_bytes(b"data")

    # 2. Create an old file (modified 50 hours ago)
    old_file = media_dir / "old_video.jpg"
    old_file.write_bytes(b"data")

    # Set modification time back 50 hours
    old_time = (datetime.now() - timedelta(hours=50)).timestamp()
    os.utime(old_file, (old_time, old_time))

    # Run pruning
    deleted_count = await media_pruner.prune_old_media()

    assert deleted_count == 1
    assert new_file.exists() is True
    assert old_file.exists() is False


@pytest.mark.asyncio
async def test_compress_old_logs(media_pruner, temp_dirs):
    """Test gzip compression of JSON logs older than 7 days."""
    _, logs_dir = temp_dirs

    # 1. Create a new log file
    new_log = logs_dir / "new_log.json"
    new_log.write_text('{"sensor_id":"soil","value":60}')

    # 2. Create an old log file (modified 8 days ago)
    old_log = logs_dir / "old_log.json"
    old_log.write_text('{"sensor_id":"soil","value":50}')
    old_time = (datetime.now() - timedelta(days=8)).timestamp()
    os.utime(old_log, (old_time, old_time))

    # Run log compression
    compressed_count = await media_pruner.compress_old_logs()

    assert compressed_count == 1
    assert new_log.exists() is True
    assert old_log.exists() is False

    gz_file = logs_dir / "old_log.json.gz"
    assert gz_file.exists() is True

    # Decompress and verify content matches
    with gzip.open(gz_file, "rt") as f:
        content = f.read()
        assert content == '{"sensor_id":"soil","value":50}'


@pytest.mark.asyncio
async def test_check_disk_usage_normal(media_pruner):
    """Test disk usage verification returns correct percentage."""
    # Mock disk usage: 100GB total, 40GB used, 60GB free
    mock_usage = lambda path: (
        100 * 1024 * 1024 * 1024,
        40 * 1024 * 1024 * 1024,
        60 * 1024 * 1024 * 1024,
    )

    with patch("shutil.disk_usage", side_effect=mock_usage):
        usage_pct = await media_pruner.check_disk_usage()
        assert usage_pct == 40.0


@pytest.mark.asyncio
async def test_check_disk_usage_critical(media_pruner):
    """Test disk usage logger triggers critical alert when over threshold."""
    # Mock disk usage: 100GB total, 90GB used (90%), 10GB free
    mock_usage = lambda path: (
        100 * 1024 * 1024 * 1024,
        90 * 1024 * 1024 * 1024,
        10 * 1024 * 1024 * 1024,
    )

    with patch("shutil.disk_usage", side_effect=mock_usage) as mock_disk:
        with patch("portal_core.media_pruner.logger.critical") as mock_critical:
            usage_pct = await media_pruner.check_disk_usage()
            assert usage_pct == 90.0
            mock_critical.assert_called_once()
            assert "Disk usage CRITICAL: 90.0%" in mock_critical.call_args[0][0]


@pytest.mark.asyncio
async def test_get_storage_stats(media_pruner, temp_dirs):
    """Test storage statistics aggregation."""
    media_dir, logs_dir = temp_dirs

    # Write files
    (media_dir / "frame1.jpg").write_bytes(b"a" * 1024 * 1024)  # 1 MB
    (logs_dir / "log1.json").write_text("b" * 1024 * 1024)  # 1 MB

    stats = media_pruner.get_storage_stats()
    assert stats["media_count"] == 1
    assert stats["logs_count"] == 1
    assert 1.9 < stats["total_size_mb"] < 2.1  # roughly 2 MB


@pytest.mark.asyncio
async def test_media_pruner_daemon_lifecycle(media_pruner):
    """Test starting and stopping background daemon task."""
    # We patch the prune/compress/check methods so it doesn't do disk access during lifecycle test
    with patch.object(media_pruner, "prune_old_media", return_value=0) as mock_prune:
        with patch.object(
            media_pruner, "compress_old_logs", return_value=0
        ) as mock_compress:
            with patch.object(
                media_pruner, "check_disk_usage", return_value=0.0
            ) as mock_check:
                original_sleep = asyncio.sleep
                reached_sleep = asyncio.Event()
                should_cancel = asyncio.Event()

                async def mock_sleep_fn(delay, *args, **kwargs):
                    if delay == 3600:
                        reached_sleep.set()
                        await should_cancel.wait()
                        raise asyncio.CancelledError()
                    return await original_sleep(delay)

                with patch(
                    "portal_core.media_pruner.asyncio.sleep", side_effect=mock_sleep_fn
                ) as mock_sleep:
                    # Start in background
                    task = asyncio.create_task(media_pruner.start())

                    # Wait until pruner hits the sleep block
                    await reached_sleep.wait()

                    assert media_pruner.is_running is True
                    mock_prune.assert_called_once()
                    mock_compress.assert_called_once()
                    mock_check.assert_called_once()

                    # Cancel pruner task
                    should_cancel.set()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                    assert media_pruner.is_running is False
