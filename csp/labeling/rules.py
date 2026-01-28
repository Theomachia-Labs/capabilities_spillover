"""Keyword-based rules labeler."""

from __future__ import annotations

import datetime
from typing import Any

from csp.data.models import Paper
from csp.labeling.core import Labeler


class KeywordLabeler(Labeler):
    """Assigns labels based on keyword matching in title/abstract."""

    SAFETY_KEYWORDS = {"safety", "robustness", "red team", "alignment", "interpretability", "bias"}
    CAPABILITY_KEYWORDS = {"state of the art", "outperform", "sota", "benchmark", "accuracy", "scale"}

    def label_paper(self, paper: Paper) -> dict[str, Any]:
        text = (paper.title + " " + (paper.abstract or "")).lower()
        
        safety_score = sum(1 for k in self.SAFETY_KEYWORDS if k in text)
        capability_score = sum(1 for k in self.CAPABILITY_KEYWORDS if k in text)

        if safety_score > 0 and capability_score == 0:
            label = "safety-use"
            confidence = 0.8
        elif capability_score > 0 and safety_score == 0:
            label = "capability-use"
            confidence = 0.8
        elif safety_score > 0 and capability_score > 0:
            label = "mixed"
            confidence = 0.6
        else:
            label = "unclear"
            confidence = 0.5

        return {
            "label_id": f"label_{paper.paper_id}_rules",
            "paper_id": paper.paper_id,
            "label": label,
            "confidence": confidence,
            "provenance": {
                "method": "rules",
                "model": "KeywordLabeler",
                "created_at": datetime.datetime.now().isoformat()
            },
            "evidence": [
                {"snippet": "Matched keywords in text."}
            ]
        }
