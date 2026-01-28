"""LLM-based labeler adapter using OpenAI API."""

from __future__ import annotations

import datetime
import json
import os
from typing import Any

from csp.data.models import Paper
from csp.labeling.core import Labeler


class LLMLabeler(Labeler):
    """Uses OpenAI API to classify paper intent."""

    SYSTEM_PROMPT = """You are an expert research analyst specializing in AI safety.
Classify research papers as one of:
- safety_use: Primarily focused on AI safety, alignment, robustness, interpretability
- capability_use: Primarily focused on advancing AI capabilities, benchmarks, SOTA
- mixed: Contains significant elements of both
- unclear: Cannot determine intent from available information

Respond ONLY with valid JSON in this format:
{"label": "...", "confidence": 0.0-1.0, "evidence": "brief explanation"}"""

    def __init__(self, model_name: str = "gpt-4o-mini", api_key: str | None = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        return self._client

    def label_paper(self, paper: Paper) -> dict[str, Any]:
        """Classify paper using OpenAI API."""
        
        user_prompt = f"""Analyze this paper:
Title: {paper.title}
Abstract: {paper.abstract or 'Not available'}

Classify the intent and provide your confidence level."""

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            label = result.get("label", "unclear")
            confidence = float(result.get("confidence", 0.5))
            evidence = result.get("evidence", "")
            
        except Exception as e:
            # Fallback on any error
            label = "unclear"
            confidence = 0.1
            evidence = f"LLM error: {str(e)}"

        return {
            "label_id": f"label_{paper.paper_id}_llm_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            "paper_id": paper.paper_id,
            "label": label,
            "confidence": confidence,
            "method": "llm",
            "audit_status": "pending" if confidence < 0.7 else "verified",
            "created_at": datetime.datetime.now().isoformat(),
            "evidence_spans": [evidence] if evidence else [],
        }
