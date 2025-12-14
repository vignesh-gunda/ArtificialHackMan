from config.models import AuditFinding, Severity
from typing import List
import re
import os

def validate_finding(finding: AuditFinding) -> List[str]:
    """Validate single finding with domain rules"""
    errors = []
    
    # Critical presence checks
    if not finding.finding_number or len(str(finding.finding_number)) < 2:
        errors.append("Invalid finding_number")
    
    if not finding.title or len(finding.title) < 5:
        errors.append("Title too short")
    
    # Confidence threshold
    threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.7))
    if finding.confidence_score < threshold:
        errors.append(f"Low confidence: {finding.confidence_score:.2f}")
    
    # Severity validation
    if finding.severity and finding.severity not in Severity.__members__.values():
        errors.append(f"Invalid severity: {finding.severity}")
    
    # URL format validation
    if finding.repository_url:
        url_pattern = r'^https?://(?:[-\w.])+(?:\:\d+)?(?:/(?:[\w/_.])*)?$'
        if not re.match(url_pattern, finding.repository_url):
            errors.append("Invalid repository_url format")
    
    # Commit ID pattern (basic)
    if finding.commit_id and len(finding.commit_id) < 7:
        errors.append("Commit ID too short")
    
    return errors