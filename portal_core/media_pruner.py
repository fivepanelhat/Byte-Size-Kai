"""
Media Pruner Module

Automated storage lifecycle management for audio and video buffers.
Prevents 24/7 capture from saturating the RPi 5's SD/NVMe storage.
"""

import asyncio
import logging
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MediaPruner:
    """
    Automated cleanup and compression of media buffers.

    - Deletes analyzed media files older than retention threshold (default 48hrs)
    - Compresses historical sensor logs to .gz format
    - Monitors disk usage and alerts if above critical threshold
    """

    def __init__(
        self,
        media_dir: str = "./telemetry_data/media",
        sensor_logs_dir: str = "./telemetry_data/sensor_logs",
        retention_hours: int = 48,
        critical_disk_usage_pct: float = 85.0,
    ):
        """
        Initialize MediaPruner.

        Args:
            media_dir: Path to audio/video buffer storage
            sensor_logs_dir: Path to historical sensor logs
            retention_hours: Keep media files for this many hours after analysis
            critical_disk_usage_pct: Alert threshold for disk utilization
        """
        self.media_dir = Path(media_dir)
        self.sensor_logs_dir = Path(sensor_logs_dir)
        self.retention_hours = retention_hours
        self.critical_disk_usage_pct = critical_disk_usage_pct
        self.is_running = False

        logger.info(
            f"MediaPruner initialized: media_dir={media_dir}, retention={retention_hours}hrs, "
            f"critical_disk_usage={critical_disk_usage_pct}%"
        )

    async def start(self):
        """Start background pruning task."""
        self.is_running = True
        logger.info("MediaPruner started")
        try:
            while self.is_running:
                await self.prune_old_media()
                await self.compress_old_logs()
                await self.check_disk_usage()
                # Run prune cycle every 1 hour
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            logger.info("MediaPruner cancelled")
            self.is_running = False

    async def stop(self):
        """Stop background pruning task."""
        self.is_running = False
        logger.info("MediaPruner stopped")

    async def prune_old_media(self) -> int:
        """
        Delete media files older than retention threshold.

        Returns:
            Number of files deleted
        """
        if not self.media_dir.exists():
            logger.warning(f"Media directory not found: {self.media_dir}")
            return 0

        deleted_count = 0
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)

        try:
            for file_path in self.media_dir.glob("*"):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    )
                    if file_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            logger.debug(
                                f"Deleted media file: {file_path.name}"
                            )
                            deleted_count += 1
                        except Exception as e:
                            logger.error(
                                f"Failed to delete {file_path.name}: {e}"
                            )

            if deleted_count > 0:
                logger.info(
                    f"MediaPruner: deleted {deleted_count} old media files"
                )

        except Exception as e:
            logger.error(f"Prune media error: {e}")

        return deleted_count

    async def compress_old_logs(self) -> int:
        """
        Compress sensor logs older than 7 days to .gz format.

        Returns:
            Number of files compressed
        """
        if not self.sensor_logs_dir.exists():
            logger.warning(
                f"Sensor logs directory not found: {self.sensor_logs_dir}"
            )
            return 0

        compressed_count = 0
        cutoff_time = datetime.now() - timedelta(days=7)

        try:
            for file_path in self.sensor_logs_dir.glob("*.json"):
                if file_path.is_file() and not file_path.name.endswith(".gz"):
                    file_mtime = datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    )
                    if file_mtime < cutoff_time:
                        try:
                            gz_path = file_path.with_suffix(".json.gz")
                            with open(file_path, "rb") as f_in:
                                with gzip.open(gz_path, "wb") as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            file_path.unlink()
                            logger.debug(
                                f"Compressed log file: {file_path.name} → {gz_path.name}"
                            )
                            compressed_count += 1
                        except Exception as e:
                            logger.error(
                                f"Failed to compress {file_path.name}: {e}"
                            )

            if compressed_count > 0:
                logger.info(
                    f"MediaPruner: compressed {compressed_count} old log files"
                )

        except Exception as e:
            logger.error(f"Compress logs error: {e}")

        return compressed_count

    async def check_disk_usage(self) -> float:
        """
        Monitor disk usage and alert if critical threshold exceeded.

        Returns:
            Current disk usage percentage
        """
        try:
            # Check disk usage for media directory's mount point
            total, used, free = shutil.disk_usage(self.media_dir)
            usage_pct = (used / total) * 100

            logger.debug(f"Disk usage: {usage_pct:.1f}%")

            if usage_pct > self.critical_disk_usage_pct:
                logger.critical(
                    f"Disk usage CRITICAL: {usage_pct:.1f}% (threshold: {self.critical_disk_usage_pct}%)"
                )

            return usage_pct

        except Exception as e:
            logger.error(f"Disk usage check error: {e}")
            return 0.0

    def get_storage_stats(self) -> dict:
        """
        Get current storage statistics.

        Returns:
            Dict with media_count, logs_count, total_size_mb
        """
        stats = {
            "media_count": 0,
            "logs_count": 0,
            "total_size_mb": 0.0,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            total_size = 0.0
            if self.media_dir.exists():
                media_files = list(self.media_dir.glob("*"))
                stats["media_count"] = len(media_files)
                media_size = sum(
                    f.stat().st_size for f in media_files if f.is_file()
                )
                total_size += media_size / (1024 * 1024)

            if self.sensor_logs_dir.exists():
                log_files = list(self.sensor_logs_dir.glob("*.json*"))
                stats["logs_count"] = len(log_files)
                logs_size = sum(
                    f.stat().st_size for f in log_files if f.is_file()
                )
                total_size += logs_size / (1024 * 1024)

            stats["total_size_mb"] = total_size

        except Exception as e:
            logger.error(f"Storage stats error: {e}")

        return stats
