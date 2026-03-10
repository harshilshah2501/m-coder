"""
Deterministic Boundary Detector — Runtime Emulator (M3.E0).

Pure rule-based boundary detection. No LLM. No inference.
Detects irreversible boundaries based on action type and boundary phrase.

Invariants:
- boundary_present NEVER produces defer (bounded_allow instead)
- shadow_mode NEVER emits boundary_verdict=crossed
"""

from __future__ import annotations

from enum import Enum


class BoundaryVerdict(str, Enum):
    """Boundary detection verdict."""
    NONE = "none"
    PRESENT = "present"
    DETECTED = "detected"
    CROSSED = "crossed"


BOUNDARY_ACTION_TYPES = frozenset({
    "merge_without_approval",
    "commit_prod_change",
    "deploy_production",
    "delete_data",
    "config_change",
    "security_override",
})

IRREVERSIBLE_KEYWORDS = frozenset({
    "production",
    "prod",
    "main",
    "master",
    "deploy",
    "merge",
    "delete",
    "drop",
    "destroy",
    "irreversible",
})


class BoundaryDetector:
    """
    Deterministic boundary detector.
    
    Detection rules:
    1. Action type in BOUNDARY_ACTION_TYPES → PRESENT
    2. Boundary phrase contains irreversible keyword → DETECTED
    3. Otherwise → NONE
    
    Shadow mode invariant:
    - In shadow mode, NEVER return CROSSED (safety constraint)
    """
    
    def detect(
        self,
        action_type: str,
        boundary_phrase: str,
        mode: str = "shadow",
    ) -> BoundaryVerdict:
        """
        Detect boundary presence/crossing.
        
        Args:
            action_type: The type of action being performed
            boundary_phrase: Description of the boundary (if any)
            mode: Execution mode ("shadow" or "live")
        
        Returns:
            BoundaryVerdict indicating boundary state
            
        Invariant: shadow mode NEVER returns CROSSED
        """
        has_boundary_action = action_type in BOUNDARY_ACTION_TYPES
        
        has_irreversible_phrase = False
        if boundary_phrase:
            phrase_lower = boundary_phrase.lower()
            for keyword in IRREVERSIBLE_KEYWORDS:
                if keyword in phrase_lower:
                    has_irreversible_phrase = True
                    break
        
        if has_boundary_action and has_irreversible_phrase:
            if mode == "shadow":
                return BoundaryVerdict.DETECTED
            return BoundaryVerdict.DETECTED
        
        if has_boundary_action:
            return BoundaryVerdict.PRESENT
        
        if has_irreversible_phrase:
            return BoundaryVerdict.DETECTED
        
        return BoundaryVerdict.NONE
