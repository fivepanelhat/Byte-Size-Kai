"""
Audio/Video Capture Module

Handles OpenCV/PyAudio streams from CSI camera and microphone.
Feeds multi-modal input to LLM and buffers raw media for historical analysis.
"""

import logging
from typing import Optional, Any

try:
    import cv2  # type: ignore
except ImportError:
    cv2 = None  # type: ignore

try:
    import pyaudio  # type: ignore
    import wave  # type: ignore
except ImportError:
    pyaudio = None  # type: ignore

logger = logging.getLogger(__name__)


class AVCapture:
    """
    Multi-modal capture: video (CSI camera) and audio (microphone).

    Manages frame/audio buffer lifecycle and exposes streams for LLM processing.
    """

    def __init__(
        self,
        camera_index: int = 0,
        video_fps: int = 30,
        audio_sample_rate: int = 16000,
        audio_chunk_size: int = 4096,
    ):
        """
        Initialize AV Capture.

        Args:
            camera_index: OpenCV camera device index (0 = /dev/video0 on Linux)
            video_fps: Target frame rate
            audio_sample_rate: Audio sample rate (Hz)
            audio_chunk_size: Audio buffer chunk size (samples)
        """
        self.camera_index = camera_index
        self.video_fps = video_fps
        self.audio_sample_rate = audio_sample_rate
        self.audio_chunk_size = audio_chunk_size

        self.video_capture: Optional[Any] = None
        self.audio_stream: Optional[Any] = None

        logger.info(
            f"AV Capture initialized: camera={camera_index}, fps={video_fps}, audio_sr={audio_sample_rate}"
        )

    async def start_video_stream(self) -> bool:
        """
        Start CSI camera stream (OpenCV).

        Returns:
            True if successful
        """
        if cv2 is None:
            logger.error("OpenCV not installed; video capture unavailable")
            return False

        try:
            self.video_capture = cv2.VideoCapture(self.camera_index)
            if not self.video_capture.isOpened():
                logger.error(
                    f"Failed to open camera device {self.camera_index}"
                )
                return False

            self.video_capture.set(cv2.CAP_PROP_FPS, self.video_fps)
            logger.info("Video stream started")
            return True
        except Exception as e:
            logger.error(f"Video capture error: {e}")
            return False

    async def start_audio_stream(self) -> bool:
        """
        Start microphone stream (PyAudio).

        Returns:
            True if successful
        """
        if pyaudio is None:
            logger.error("PyAudio not installed; audio capture unavailable")
            return False

        try:
            pa = pyaudio.PyAudio()
            self.audio_stream = pa.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.audio_sample_rate,
                input=True,
                frames_per_buffer=self.audio_chunk_size,
            )
            logger.info("Audio stream started")
            return True
        except Exception as e:
            logger.error(f"Audio capture error: {e}")
            return False

    async def capture_frame(self) -> Optional[bytes]:
        """
        Capture single video frame.

        Returns:
            JPEG-encoded frame bytes, or None on error
        """
        if self.video_capture is None or not self.video_capture.isOpened():
            logger.warning("Video capture not initialized")
            return None

        try:
            ret, frame = self.video_capture.read()
            if ret:
                _, jpeg_data = cv2.imencode(".jpg", frame)
                logger.debug(f"Frame captured: {jpeg_data.nbytes} bytes")
                return jpeg_data.tobytes()
            else:
                logger.warning("Failed to capture frame")
                return None
        except Exception as e:
            logger.error(f"Frame capture error: {e}")
            return None

    async def capture_audio_chunk(self) -> Optional[bytes]:
        """
        Capture single audio chunk.

        Returns:
            WAV-encoded audio bytes, or None on error
        """
        if self.audio_stream is None:
            logger.warning("Audio capture not initialized")
            return None

        try:
            audio_data = self.audio_stream.read(
                self.audio_chunk_size, exception_on_overflow=False
            )
            logger.debug(f"Audio chunk captured: {len(audio_data)} bytes")
            return audio_data
        except Exception as e:
            logger.error(f"Audio capture error: {e}")
            return None

    async def stop(self):
        """Stop all captures and clean up resources."""
        try:
            if self.video_capture:
                self.video_capture.release()
                self.video_capture = None
                logger.info("Video stream stopped")
        except Exception as e:
            logger.error(f"Error stopping video capture: {e}")

        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
                logger.info("Audio stream stopped")
        except Exception as e:
            logger.error(f"Error stopping audio capture: {e}")

    async def health_check(self) -> bool:
        """
        Verify both video and audio streams are available.

        Returns:
            True if both streams are operational (or graceful degradation if one fails)
        """
        try:
            video_ok = False
            audio_ok = False

            # Check video capture
            if self.video_capture is not None:
                try:
                    video_ok = self.video_capture.isOpened()
                except Exception as e:
                    logger.warning(f"Video stream health check failed: {e}")
                    video_ok = False

            # Check audio stream
            if self.audio_stream is not None:
                try:
                    audio_ok = self.audio_stream.is_active()
                except Exception as e:
                    logger.warning(f"Audio stream health check failed: {e}")
                    audio_ok = False

            # Consider healthy if at least one stream is active (graceful degradation)
            # Or if streams haven't been initialized yet
            is_healthy = (
                video_ok
                or audio_ok
                or (self.video_capture is None and self.audio_stream is None)
            )

            logger.info(
                f"AV health: video={video_ok}, audio={audio_ok}, overall={is_healthy}"
            )
            return is_healthy

        except Exception as e:
            logger.error(f"AV health check error: {e}")
            return False
