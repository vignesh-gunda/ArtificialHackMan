from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class Severity(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    WARNING = "Warning"
    INFO = "Info"

class AuditFinding(BaseModel):
    """Structured audit finding with validation"""
    finding_number: str = Field(..., description="Unique finding identifier")
    title: str = Field(..., min_length=5)
    status: Optional[str] = None
    severity: Optional[Severity] = None
    impact: Optional[str] = None
    likelihood: Optional[str] = None
    description: Optional[str] = Field(None, min_length=10)
    recommendation: Optional[str] = None
    repository_url: Optional[str] = Field(None, pattern=r"^https?://")
    commit_id: Optional[str] = None
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    extraction_attempts: int = 0
    additional_fields: Optional[dict] = None
    
    class Config:
        use_enum_values = True

class ExtractionResult(BaseModel):
    """Wrapper for complete extraction results"""
    filename: str
    findings: List[AuditFinding] = []
    total_findings: int = 0
    validation_errors: List[str] = []
    requires_human_review: bool = False
    extraction_timestamp: datetime = Field(default_factory=datetime.now)