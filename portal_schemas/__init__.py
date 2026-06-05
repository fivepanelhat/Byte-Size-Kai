"""
Blue Moon Portal Schemas

Pydantic models for strict JSON schema enforcement.
Prevents LLM hallucinations from breaking hardware execution loops.
"""

from .ai_models import CropOptimizationPlan, SensorReading, AnalysisResult

__all__ = ["CropOptimizationPlan", "SensorReading", "AnalysisResult"]
