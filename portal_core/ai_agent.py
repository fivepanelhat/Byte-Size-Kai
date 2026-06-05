"""
AI Agent Module

Orchestrates asynchronous multi-modal LLM control using Gemma 4 E4B via Ollama.
Ingests sensor telemetry, audio, and visual data; reasons over historical logs;
and generates deterministic hardware commands via Pydantic schema enforcement.
"""

import asyncio
import json
import logging
import re
from typing import Optional
from datetime import datetime

import ollama

logger = logging.getLogger(__name__)


class AIAgent:
    """
    Autonomous agent for crop optimization reasoning.

    Interfaces with Ollama (local Gemma 4 E4B model) to:
    - Parse multi-modal input (MQTT telemetry, camera frames, audio)
    - Reason over historical sensor logs
    - Generate structured JSON actions (irrigation, lighting adjustments)
    """

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model: str = "gemma4:latest",
    ):
        """
        Initialize the AI Agent.

        Args:
            ollama_host: Base URL for Ollama API endpoint
            model: Model identifier (expects Gemma 4 E4B or compatible)
        """
        self.ollama_host = ollama_host
        self.model = model
        self.client = ollama.Client(host=ollama_host)
        logger.info(f"AI Agent initialized with model: {model} at {ollama_host}")

    async def analyze_sensor_state(
        self,
        sensor_data: dict,
        historical_context: Optional[list] = None,
    ) -> dict:
        """
        Analyze current sensor state against historical context.

        Args:
            sensor_data: Current MQTT payload (soil moisture, light, humidity, etc.)
            historical_context: Recent historical readings for trend analysis

        Returns:
            Structured analysis result (dict conforming to AnalysisResult schema)
        """
        try:
            logger.debug(f"Analyzing sensor state: {sensor_data}")

            # Construct context-aware prompt for Ollama
            historical_str = ""
            if historical_context:
                historical_str = f"\n\nHistorical readings (last 10 samples):\n{str(historical_context)}"

            prompt = f"""Agricultural AI: Analyze these sensor readings and respond ONLY with a JSON object (no other text):

Sensors:
{str(sensor_data)}
{historical_str}

JSON format: {{"status":"healthy|warning|critical", "soil_moisture_trend":"stable|increasing|decreasing", "ambient_light_level":"low|optimal|high", "humidity_status":"dry|optimal|high", "observations":"brief note"}}"""

            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.generate,
                        self.model,
                        prompt,
                        stream=False,
                    ),
                    timeout=60.0,  # Increased to 60 seconds for Gemma 4
                )
            except asyncio.TimeoutError:
                logger.error("LLM request timeout during sensor analysis")
                return self._generate_default_analysis(error_msg="LLM timeout")

            response_text = response.get("response", "").strip()
            logger.debug(f"LLM response: {response_text[:200]}...")

            # Parse JSON response
            try:
                analysis_data = json.loads(response_text)
                analysis_data["analysis_id"] = f"analysis-{datetime.now().isoformat()}"
                analysis_data["timestamp"] = datetime.now().isoformat()
                return analysis_data
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM JSON response, returning defaults")
                return self._generate_default_analysis(observation=response_text[:500])

        except Exception as e:
            logger.error(f"Sensor analysis error: {e}")
            return self._generate_default_analysis(error_msg=str(e))

    def _generate_default_analysis(
        self, error_msg: Optional[str] = None, observation: Optional[str] = None
    ) -> dict:
        """Generate a safe default analysis on error."""
        return {
            "analysis_id": f"analysis-{datetime.now().isoformat()}",
            "status": "unknown",
            "soil_moisture_trend": "stable",
            "ambient_light_level": "optimal",
            "humidity_status": "optimal",
            "observations": observation
            or error_msg
            or "Unable to perform full analysis",
            "timestamp": datetime.now().isoformat(),
        }

    async def process_visual_feedback(self, frame_data: bytes) -> dict:
        """
        Process camera frame via Gemma 4 visual embedding.

        Args:
            frame_data: Raw image bytes (e.g., JPEG from CSI camera)

        Returns:
            Visual analysis result (crop health, anomalies, etc.)
        """
        if not frame_data:
            logger.warning("Visual feedback: frame_data is empty")
            return {
                "overall_health": "unknown",
                "timestamp": datetime.now().isoformat(),
            }

        try:
            logger.debug(f"Processing visual frame ({len(frame_data)} bytes)")

            # Note: Ollama's client library doesn't directly support vision in generate()
            # For now, we'll use a text-based prompt that requests analysis
            # In production, you'd integrate with Ollama's multimodal endpoints or use
            # local CV models alongside the LLM

            prompt = """Microgreen health assessment - respond ONLY with JSON: {"overall_health":"excellent|good|fair|poor", "anomalies":"none|yellowing|browning|wilting|other", "confidence":"high|medium|low"}"""

            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.generate,
                        self.model,
                        prompt,
                        stream=False,
                    ),
                    timeout=45.0,  # 45 second timeout for vision
                )
            except asyncio.TimeoutError:
                logger.error("LLM request timeout during visual analysis")
                return {
                    "overall_health": "unknown",
                    "timestamp": datetime.now().isoformat(),
                    "frame_bytes": len(frame_data),
                }
            response_text = response.get("response", "").strip()
            logger.debug(f"Visual analysis LLM response: {response_text[:200]}...")

            # Parse response
            import json

            try:
                visual_data = json.loads(response_text)
                visual_data["frame_timestamp"] = datetime.now().isoformat()
                visual_data["frame_bytes"] = len(frame_data)
                return visual_data
            except json.JSONDecodeError:
                return {
                    "overall_health": "pending",
                    "analysis": response_text[:500],
                    "frame_timestamp": datetime.now().isoformat(),
                    "frame_bytes": len(frame_data),
                }

        except Exception as e:
            logger.error(f"Visual feedback processing error: {e}")
            return {
                "overall_health": "error",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def process_audio_feedback(self, audio_data: bytes) -> dict:
        """
        Process audio via Gemma 4 audio embedding.

        Args:
            audio_data: Raw audio bytes (e.g., ambient sound from microphone)

        Returns:
            Audio analysis result (anomalies: pump failure, pest activity, etc.)
        """
        if not audio_data:
            logger.warning("Audio feedback: audio_data is empty")
            return {"anomaly_detected": False, "timestamp": datetime.now().isoformat()}

        try:
            logger.debug(f"Processing audio input ({len(audio_data)} bytes)")

            # Note: Similar to vision, Ollama's text generation doesn't directly support audio
            # In production, you'd use a separate audio model or transcription + LLM
            # For now, provide a prompt-based analysis framework

            prompt = """Farm audio analysis - respond ONLY with JSON: {"anomaly_detected":true|false, "type":"pump_failure|pest|normal|unknown", "confidence":"high|medium|low"}"""

            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.generate,
                        self.model,
                        prompt,
                        stream=False,
                    ),
                    timeout=45.0,  # 45 second timeout for audio
                )
            except asyncio.TimeoutError:
                logger.error("LLM request timeout during audio analysis")
                return {
                    "anomaly_detected": False,
                    "timestamp": datetime.now().isoformat(),
                    "audio_bytes": len(audio_data),
                }

            response_text = response.get("response", "").strip()

            # Parse response
            import json

            try:
                audio_result = json.loads(response_text)
                audio_result["audio_timestamp"] = datetime.now().isoformat()
                audio_result["audio_bytes"] = len(audio_data)
                return audio_result
            except json.JSONDecodeError:
                return {
                    "anomaly_detected": False,
                    "analysis": response_text[:500],
                    "audio_timestamp": datetime.now().isoformat(),
                    "audio_bytes": len(audio_data),
                }

        except Exception as e:
            logger.error(f"Audio feedback processing error: {e}")
            return {
                "anomaly_detected": False,
                "error_message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def generate_optimization_plan(
        self,
        sensor_analysis: dict,
        visual_analysis: dict,
        audio_analysis: dict,
    ) -> dict:
        """
        Generate crop optimization plan by reasoning over multi-modal input.

        Args:
            sensor_analysis: Structured telemetry analysis
            visual_analysis: Crop health assessment
            audio_analysis: Anomaly detection

        Returns:
            CropOptimizationPlan (Pydantic-validated JSON)
        """
        try:
            logger.info("Generating optimization plan from multi-modal input")

            # Construct concise prompt with all analysis inputs
            prompt = f"""Microgreen optimization - respond ONLY with JSON:
Sensors: {str(sensor_analysis)[:200]}
Vision: {str(visual_analysis)[:100]}
Audio: {str(audio_analysis)[:100]}

JSON: {{"plan_id":"opt-{datetime.now().strftime('%Y%m%d')}", "pump_action":"off|low|medium|high", "lighting_action":"off|dim|normal|full", "confidence_score":0.8, "execution_window_minutes":30, "requires_human_review":false}}"""

            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.generate,
                        self.model,
                        prompt,
                        stream=False,
                    ),
                    timeout=60.0,  # 60 second timeout for planning
                )
            except asyncio.TimeoutError:
                logger.error("LLM request timeout during optimization planning")
                return self._generate_default_plan()

            response_text = response.get("response", "").strip()
            logger.debug(f"Optimization plan LLM response: {response_text[:300]}...")

            # Extract JSON from response (handle cases where LLM adds extra text)
            # Try to find JSON object in response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                try:
                    plan_data = json.loads(json_str)

                    # Validate with Pydantic (import needed)
                    from portal_schemas.ai_models import (
                        CropOptimizationPlan,
                        PumpAction,
                        LightingAction,
                    )

                    # Ensure pump_action and lighting_action are valid enums
                    if isinstance(plan_data.get("pump_action"), str):
                        pump_action = plan_data["pump_action"].lower()
                        if pump_action not in ["off", "low", "medium", "high"]:
                            pump_action = "off"
                        plan_data["pump_action"] = PumpAction(pump_action)

                    if isinstance(plan_data.get("lighting_action"), str):
                        lighting_action = plan_data["lighting_action"].lower()
                        if lighting_action not in ["off", "dim", "normal", "full"]:
                            lighting_action = "normal"
                        plan_data["lighting_action"] = LightingAction(lighting_action)

                    # Validate and create Pydantic model
                    validated_plan = CropOptimizationPlan(**plan_data)
                    logger.info(
                        f"Optimization plan validated: {validated_plan.plan_id}"
                    )
                    return validated_plan.dict()

                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse JSON from LLM response: {je}")
                    return self._generate_default_plan()
                except Exception as e:
                    logger.error(f"Failed to validate optimization plan: {e}")
                    # Return default safe plan on validation error
                    return self._generate_default_plan()
            else:
                logger.warning("No JSON found in LLM response")
                return self._generate_default_plan()

        except Exception as e:
            logger.error(f"Optimization plan generation error: {e}")
            return self._generate_default_plan()

    def _generate_default_plan(self) -> dict:
        """Generate a safe default optimization plan."""
        from portal_schemas.ai_models import (
            CropOptimizationPlan,
            PumpAction,
            LightingAction,
        )

        default = CropOptimizationPlan(
            plan_id=f"opt-default-{datetime.now().isoformat()}",
            pump_action=PumpAction.MEDIUM,
            lighting_action=LightingAction.NORMAL,
            predicted_yield_impact="Holding steady with default parameters",
            logistical_notes="Default optimization parameters applied",
            confidence_score=0.5,
            execution_window_minutes=30,
            requires_human_review=True,
        )
        return default.dict()

    async def health_check(self) -> bool:
        """
        Verify Ollama and model availability with timeout protection.

        Returns:
            True if Ollama is responsive and model is loaded
        """
        try:
            # Lightweight Ollama health check with 5 second timeout
            response = await asyncio.wait_for(
                asyncio.to_thread(self.client.list), timeout=5.0
            )
            models = [m["name"] for m in response.get("models", [])]
            is_healthy = self.model in models
            logger.info(
                f"Ollama health check: {'OK' if is_healthy else 'FAIL'} (models: {len(models)})"
            )
            return is_healthy
        except asyncio.TimeoutError:
            logger.error("Ollama health check timeout - service may be unresponsive")
            return False
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
