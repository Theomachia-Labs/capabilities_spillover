"""Labeling interface."""

from __future__ import annotations

import abc
from typing import Any

from csp.data.models import Paper

class Labeler(abc.ABC):
    """Abstract base class for paper labelers."""

    @abc.abstractmethod
    def label_paper(self, paper: Paper) -> dict[str, Any]:
        """Generate a LabelRecord for a given paper.
        
        Returns a dictionary compatible with label_record schema.
        """
        pass
