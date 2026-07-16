# Byte Size Kai - Changelog

## 1.3.0 - 2026-07-16

### Repository rename
- GitHub repository renamed: `Blue-Moon-Portal` -> `Byte-Size-Kai`
- Product and repo name unified as **Byte Size Kai**
- Old URL redirects on GitHub for existing clones/links
- Package: `byte_size_kai`; CLI: `byte-size-kai` (`blue-moon-portal` kept as alias)
- Class: `ByteSizeKaiPortal` (`BlueMoonPortal` / `BlueMonPortal` aliases for tests)

## Version 1.3.0 - 2026-07-10

### Fixed
- Restored complete `main.py` lifecycle (`start` / `stop` / health / pruner / CLI entry).
- Exception-safe multimodal gather (failed frame/audio no longer poison the plan path).

### Changed / optimised (edge)
- Plan rate limiting via `BLUE_MOON_MIN_PLAN_INTERVAL_SEC` (default 30s).
- Optional adaptive AV skip when sensors are stable (`BLUE_MOON_ADAPTIVE_AV`).
- Compact flywheel outcome metadata + JSONL rotation on size.
- Prefer `opencv-python-headless` for Pi deployments.
- Removed non-product `track_and_zap.py` Colab export; ignore flywheel JSONL data files.

---
## Version 1.2.0 - 2026-06-08

- Aligned project with Coastal Alpine Stack version 1.2.0.
- Upgraded configuration schemas.

## Version 0.1.0 - Initial Implementation Complete ✓

### Major Features Implemented

#### 1. AI Agent with Ollama Integration ✓

- **Status**: Complete
- Full LLM integration with Ollama for crop optimization reasoning
- Implemented methods:
  - `analyze_sensor_state()` - Multi-modal sensor analysis with trend detection
  - `process_visual_feedback()` - Crop health assessment from camera frames
  - `process_audio_feedback()` - Anomaly detection from microphone input
  - `generate_optimization_plan()` - Pydantic-validated action planning
  - `health_check()` - Ollama connectivity verification
- Features:
  - Timeout protection on all LLM calls (10-30 second timeouts)
  - Graceful fallback to default responses on timeout/error
  - JSON response parsing with error recovery
  - Schema validation via Pydantic

#### 2. Hardware Control System ✓

- **Status**: Complete
- GPIO-based actuator control with graceful degradation
- Implemented:
  - Pump control (OFF, LOW, MEDIUM, HIGH states with PWM)
  - Lighting control (OFF, DIM, NORMAL, FULL with PWM)
  - Alert/buzzer system
  - Simulation mode for development (no actual GPIO required)
  - Action history tracking for auditing
  - Support for Raspberry Pi 5 GPIO and RPi.GPIO library
- Features:
  - Automatic fallback to simulation when GPIO unavailable
  - Clean GPIO setup/cleanup with exception handling
  - Duty cycle mapping for smooth control
  - `enforce_plan()` method to execute optimization plans

#### 3. Configuration Management ✓

- **Status**: Complete
- Pydantic-based configuration validation
- Implemented:
  - Environment variable loading with type checking
  - Default values for all configuration
  - Automatic directory creation
  - Configuration printing for debugging
  - Comprehensive .env.example template
- Sub-configurations:
  - OllamaConfig: LLM settings
  - MQTTConfig: Broker connection
  - StorageConfig: Media lifecycle
  - CameraConfig: Video capture
  - AudioConfig: Audio capture
  - HardwareConfig: GPIO control
  - LoggingConfig: Output settings

#### 4. MQTT Client Enhancement ✓

- **Status**: Complete
- Improved async MQTT subscription with retry logic
- Implemented:
  - Exponential backoff retry strategy (3 attempts)
  - Async connection with proper timeout handling
  - Message queue buffering
  - Connection state tracking
  - Automatic subscription to sensor topics

#### 5. AV Capture Enhancement ✓

- **Status**: Complete
- Improved health check with graceful degradation
- Implemented:
  - Dual stream support (video + audio)
  - Exception-safe stream initialization
  - Stream state verification
  - Support for optional streams (one stream = success)
  - Proper exception handling for missing libraries

#### 6. Media Pruner ✓

- **Status**: Complete
- Storage lifecycle management
- Implemented:
  - Automatic old media deletion
  - Log compression (.gz)
  - Disk usage monitoring
  - Critical threshold alerting
  - Storage statistics reporting

#### 7. Error Handling & Resilience ✓

- **Status**: Complete
- Comprehensive error handling throughout codebase
- Implemented:
  - Timeout protection on all async operations
  - Default fallback responses for failures
  - Exception logging with full context
  - Graceful degradation (e.g., no camera = telemetry-only mode)
  - Retry logic for network operations
  - Health check verification before startup

#### 8. System Validation & Testing ✓

- **Status**: Complete
- `validate.py` script for pre-deployment verification
- Tests:
  - Configuration validation
  - Ollama connectivity
  - MQTT broker connectivity
  - AV capture initialization
  - Hardware control setup
  - Media pruner functionality
  - AI Agent method execution
- Output:
  - Color-coded test results
  - Component status summary
  - Ready/not-ready determination

#### 9. Documentation ✓

- **Status**: Complete
- GETTING_STARTED.md guide covering:
  - Quick start setup
  - Component architecture
  - Data flow diagrams
  - Development workflow
  - Production deployment on RPi 5
  - Troubleshooting guide
  - Performance tuning
- Updated .env.example with extensive comments
- Comprehensive docstrings on all classes/methods

### Bug Fixes & Improvements

- Fixed: AV Capture health check returning false when streams not initialized
- Fixed: MQTT connection not handling connection failures
- Fixed: AI Agent methods without timeout protection
- Fixed: Missing error handling in optimization plan generation
- Fixed: Configuration variables not consistently applied
- Improved: JSON response parsing with regex extraction
- Improved: Logging throughout all components
- Improved: Exception handling with graceful fallbacks

### Files Added

1. **portal_core/config.py** - Configuration management (285 lines)
2. **portal_core/hardware_control.py** - Hardware actuator control (445 lines)
3. **validate.py** - System validation script (340 lines)
4. **GETTING_STARTED.md** - Development & deployment guide (410 lines)

### Files Modified

1. **portal_core/ai_agent.py** - Full LLM integration (270 lines of implementation)
2. **portal_core/mqtt_client.py** - Connection retry logic
3. **portal_core/av_capture.py** - Improved health check
4. **portal_core/**init**.py** - Updated exports
5. **main.py** - Config integration, hardware enforcement
6. **.env.example** - Expanded documentation

### Code Statistics

- **Total new lines**: ~1,750
- **Components fully implemented**: 8/8
- **Test coverage**: Configuration, Ollama, MQTT, AV, Hardware, MediaPruner, AI Agent
- **Error handling**: Comprehensive exception handling throughout
- **Documentation**: 1,500+ lines of docstrings and guides

### Architecture Improvements

1. **Modularity**: Clean separation of concerns
2. **Type Safety**: Pydantic validation throughout
3. **Async Design**: Full async/await pattern
4. **Resilience**: Timeout protection and graceful degradation
5. **Testing**: Comprehensive validation script
6. **Observability**: Detailed logging at all levels

### Production Readiness

✓ Configuration validation  
✓ Error handling & recovery  
✓ Health checks for all components  
✓ Retry logic for network operations  
✓ Timeout protection for LLM calls  
✓ GPIO simulation mode for dev/testing  
✓ Systemd service template provided  
✓ Comprehensive documentation  
✓ Validation script for pre-deployment  

### Known Limitations

1. **Vision/Audio Processing**: Ollama text generation doesn't natively support vision/audio
   - Current: Text-based prompts for image/audio analysis
   - Future: Integrate specialized vision/audio models or transcription

2. **MQTT Security**: Currently supports no auth or basic auth
   - Future: TLS/SSL certificate support

3. **Database**: No persistent state storage
   - Future: Add SQLite/PostgreSQL for historical data

4. **Alerting**: Basic console logging
   - Future: Email/Slack notifications via webhooks

### Next Steps (Phase 2)

- [ ] Implement dedicated vision model integration
- [ ] Add audio transcription for better anomaly detection
- [ ] Build crop monitoring dashboard
- [ ] Implement yield prediction model
- [ ] Add email/Slack alerting
- [ ] Create REST API for remote monitoring
- [ ] Implement autonomous learning/retraining
- [ ] Add multi-crop support
- [ ] Implement data export/reporting

### Testing Checklist

- [x] Configuration loading and validation
- [x] Ollama LLM connectivity and health check
- [x] MQTT connection with retry logic
- [x] AV capture initialization (graceful degradation)
- [x] Hardware control setup and simulation mode
- [x] Media pruner storage management
- [x] AI Agent sensor analysis
- [x] Optimization plan generation
- [x] Plan enforcement with hardware control
- [x] Error handling and timeouts

### Deployment Checklist

- [x] All core functionality implemented
- [x] Error handling and resilience
- [x] Configuration validation
- [x] System health checks
- [x] Validation script
- [x] Documentation
- [x] Example environment configuration
- [x] Graceful degradation support
- [ ] Systemd service deployment (documented, ready to configure)
- [ ] RPi 5 hardware setup (instructions provided)

---

## Support & Contributing

For issues or questions:

- Review GETTING_STARTED.md
- Run validate.py to check system health
- Check logs for detailed error messages
- See DEVELOPMENT.md for detailed architecture

---

**Project Status**: MVP Ready ✓
**Version**: 0.1.0-alpha
**Last Updated**: 2026-06-01
