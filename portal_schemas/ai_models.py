"""
AI Models Module

Pydantic schemas for strict JSON enforcement.
Ensures LLM output conforms to deterministic hardware command structures.
"""

from typing import Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class PumpAction(str, Enum):
 """Enumeration of valid pump commands."""

 OFF = "off"
 LOW = "low"
 MEDIUM = "medium"
 HIGH = "high"


class LightingAction(str, Enum):
 """Enumeration of valid lighting commands."""

 OFF = "off"
 DIM = "dim"
 NORMAL = "normal"
 FULL = "full"


class SensorReading(BaseModel):
 """
 Single sensor telemetry point.

 Represents a timestamped measurement from the edge hardware.
 """

 sensor_id: str = Field(
 ..., description="Unique sensor identifier (e.g., 'soil_moisture_1')"
 )
 sensor_type: str = Field(
 ...,
 description="Sensor type (e.g., 'capacitive_moisture', 'ambient_light')",
 )
 value: float = Field(..., description="Measured value")
 unit: str = Field(
 ..., description="Unit of measurement (e.g., 'V', 'lux', '%RH')"
 )
 timestamp: datetime = Field(default_factory=datetime.now)


class AnalysisResult(BaseModel):
 """
 Result of multi-modal sensor analysis.

 Intermediate representation after LLM processes sensor telemetry.
 """

 analysis_id: str = Field(..., description="Unique analysis ID")
 status: str = Field(
 ...,
 description="Status assessment (e.g., 'healthy', 'warning', 'critical')",
 )
 soil_moisture_trend: str = Field(
 ...,
 description="Trend direction ('stable', 'increasing', 'decreasing')",
 )
 ambient_light_level: str = Field(
 ..., description="Light condition ('low', 'optimal', 'high')"
 )
 humidity_status: str = Field(
 ..., description="Humidity status ('dry', 'optimal', 'high')"
 )
 visual_observations: Optional[str] = Field(
 None, description="Crop health observations from camera feed"
 )
 audio_observations: Optional[str] = Field(
 None,
 description="Environmental anomalies from audio (pump failure, pest activity, etc.)",
 )
 timestamp: datetime = Field(default_factory=datetime.now)


class CropOptimizationPlan(BaseModel):
 """
 Deterministic hardware action plan.

 Output schema enforced by Pydantic. LLM generates JSON matching this structure;
 if it doesn't conform, parsing fails and prevents invalid hardware commands.
 """

 plan_id: str = Field(..., description="Unique plan identifier")
 generated_at: datetime = Field(default_factory=datetime.now)

 # Hardware actions
 pump_action: PumpAction = Field(
 ..., description="Pump command (off, low, medium, high)"
 )
 lighting_action: LightingAction = Field(
 ..., description="Lighting command (off, dim, normal, full)"
 )

 # Predictions and reasoning
 predicted_yield_impact: Optional[str] = Field(
 None,
 description="Predicted impact on harvest yield (e.g., '+5% maturation speedup')",
 )
 logistical_notes: Optional[str] = Field(
 None, description="Harvest timing and resource requirements"
 )
 confidence_score: float = Field(
 ...,
 ge=0.0,
 le=1.0,
 description="LLM confidence in this plan (0.0-1.0)",
 )

 # Execution metadata
 execution_window_minutes: int = Field(
 ..., description="Recommended time window to execute actions (minutes)"
 )
 requires_human_review: bool = Field(
 default=False,
 description="Flag if plan requires human approval before enforcement",
 )

 model_config = ConfigDict(
 json_schema_extra={
 "example": {
 "plan_id": "opt-2026-05-31-001",
 "generated_at": "2026-05-31T23:45:00Z",
 "pump_action": "medium",
 "lighting_action": "normal",
 "predicted_yield_impact": "+3% maturation speedup",
 "logistical_notes": "Expect harvest in 5 days; prepare logistics for 120kg microgreens",
 "confidence_score": 0.87,
 "execution_window_minutes": 30,
 "requires_human_review": False,
 }
 }
 )
