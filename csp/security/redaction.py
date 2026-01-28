"""Safety redaction module for public artifacts."""

from __future__ import annotations
import re

# List of sensitive terms or patterns to redact
# In a real system, this would be a loaded configuration or model-based filter
SENSITIVE_PATTERNS = [
    r"exploit[:\s]+code",
    r"vulnerability[:\s]+steps",
    r"attack[:\s]+vector[:\s]+detailed",
    r"jailbreak[:\s]+prompt",
]

SENSITIVE_KEYWORDS = [
    "[REDACTED]", 
]

class Redactor:
    """Handles redaction of sensitive information from text."""
    
    def __init__(self, patterns: list[str] | None = None):
        self.patterns = patterns or SENSITIVE_PATTERNS
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.patterns]
        
    def redact_text(self, text: str) -> str:
        """Redact sensitive patterns from text."""
        if not text:
            return ""
            
        redacted = text
        for pattern in self.compiled_patterns:
            redacted = pattern.sub("[REDACTED]", redacted)
            
        return redacted

    def redact_summary(self, summary: str) -> str:
        """Special handling for summaries."""
        # For now, just apply text redaction
        # Could add logic to remove whole sentences if density is high
        return self.redact_text(summary)
