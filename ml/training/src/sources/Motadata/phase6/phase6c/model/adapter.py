"""
Model adapter interface: consume messages (with origin tags), return response dict.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ModelAdapter(ABC):
    """Abstract adapter for step execution: messages in → response dict out."""

    @abstractmethod
    def generate(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        messages: list of {"role": str, "content": str, "origin": str (optional)}.
        Returns e.g. {"content": str, "model": str, "tokens": int}.
        """
        ...
