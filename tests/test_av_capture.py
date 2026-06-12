import pytest
from unittest.mock import MagicMock, patch
from portal_core.av_capture import AVCapture


@pytest.fixture
def av_capture():
    return AVCapture(
        camera_index=0,
        video_fps=30,
        audio_sample_rate=16000,
        audio_chunk_size=4096,
    )


@pytest.mark.asyncio
async def test_av_capture_init(av_capture):
    """Test initialization settings."""
    assert av_capture.camera_index == 0
    assert av_capture.video_fps == 30
    assert av_capture.audio_sample_rate == 16000
    assert av_capture.audio_chunk_size == 4096
    assert av_capture.video_capture is None
    assert av_capture.audio_stream is None


@pytest.mark.asyncio
async def test_start_video_stream_success(av_capture):
    """Test video stream initialization with OpenCV installed and responsive."""
    with patch("portal_core.av_capture.cv2") as mock_cv2:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cv2.VideoCapture.return_value = mock_cap

        success = await av_capture.start_video_stream()
        assert success is True
        assert av_capture.video_capture == mock_cap
        mock_cap.set.assert_called_once()


@pytest.mark.asyncio
async def test_start_video_stream_not_opened(av_capture):
    """Test video stream initialization when camera cannot be opened."""
    with patch("portal_core.av_capture.cv2") as mock_cv2:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cv2.VideoCapture.return_value = mock_cap

        success = await av_capture.start_video_stream()
        assert success is False


@pytest.mark.asyncio
async def test_start_video_stream_no_cv2(av_capture):
    """Test video stream initialization when OpenCV is not installed."""
    with patch("portal_core.av_capture.cv2", None):
        success = await av_capture.start_video_stream()
        assert success is False


@pytest.mark.asyncio
async def test_start_audio_stream_no_pyaudio(av_capture):
    """Test audio stream initialization when PyAudio is not installed (expected in dev environment)."""
    with patch("portal_core.av_capture.pyaudio", None):
        success = await av_capture.start_audio_stream()
        assert success is False


@pytest.mark.asyncio
async def test_start_audio_stream_success(av_capture):
    """Test audio stream initialization with mock PyAudio."""
    with patch("portal_core.av_capture.pyaudio") as mock_pa:
        mock_pa_inst = MagicMock()
        mock_stream = MagicMock()
        mock_pa.PyAudio.return_value = mock_pa_inst
        mock_pa_inst.open.return_value = mock_stream

        success = await av_capture.start_audio_stream()
        assert success is True
        assert av_capture.audio_stream == mock_stream


@pytest.mark.asyncio
async def test_capture_frame_success(av_capture):
    """Test capturing a frame successfully."""
    with patch("portal_core.av_capture.cv2") as mock_cv2:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, "frame_data")
        av_capture.video_capture = mock_cap

        mock_cv2.imencode.return_value = (
            True,
            MagicMock(tobytes=lambda: b"jpeg_bytes", nbytes=10),
        )

        frame = await av_capture.capture_frame()
        assert frame == b"jpeg_bytes"
        mock_cap.read.assert_called_once()


@pytest.mark.asyncio
async def test_capture_frame_failed(av_capture):
    """Test frame capture failure."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (False, None)
    av_capture.video_capture = mock_cap

    frame = await av_capture.capture_frame()
    assert frame is None


@pytest.mark.asyncio
async def test_capture_audio_chunk(av_capture):
    """Test capturing an audio chunk."""
    mock_stream = MagicMock()
    mock_stream.read.return_value = b"audio_chunk_bytes"
    av_capture.audio_stream = mock_stream

    chunk = await av_capture.capture_audio_chunk()
    assert chunk == b"audio_chunk_bytes"
    mock_stream.read.assert_called_once_with(4096, exception_on_overflow=False)


@pytest.mark.asyncio
async def test_stop(av_capture):
    """Test clean stopping and resource release."""
    mock_cap = MagicMock()
    mock_stream = MagicMock()

    av_capture.video_capture = mock_cap
    av_capture.audio_stream = mock_stream

    await av_capture.stop()

    mock_cap.release.assert_called_once()
    mock_stream.stop_stream.assert_called_once()
    mock_stream.close.assert_called_once()
    assert av_capture.video_capture is None
    assert av_capture.audio_stream is None


@pytest.mark.asyncio
async def test_health_check_states(av_capture):
    """Test health check states under different active streams."""
    # 1. Uninitialized is considered healthy (degraded/not-yet-started)
    assert await av_capture.health_check() is True

    # 2. Both streams mock active
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    av_capture.video_capture = mock_cap

    mock_stream = MagicMock()
    mock_stream.is_active.return_value = True
    av_capture.audio_stream = mock_stream

    assert await av_capture.health_check() is True

    # 3. Video inactive, audio active (graceful degradation)
    mock_cap.isOpened.return_value = False
    assert await av_capture.health_check() is True

    # 4. Both streams inactive
    mock_stream.is_active.return_value = False
    assert await av_capture.health_check() is False
