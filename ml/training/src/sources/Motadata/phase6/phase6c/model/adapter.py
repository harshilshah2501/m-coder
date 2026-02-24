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

    def model_id(self) -> str:
        """
        Stable identifier for this adapter / underlying model.

        Default implementation falls back to an optional MODEL_ID attribute
        or the class name if not provided.
        """
        model_id = getattr(self, "MODEL_ID", self.__class__.__name__)
        return str(model_id)
