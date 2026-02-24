# Phase-6C injection profiles (wrappers). No governance/seed mutation.
from .types import WrapperState, InjectionProfile
from .profiles import get_profile, list_profile_ids, CANONICAL_PROFILE_IDS
from .wrapper import apply_wrapper

__all__ = [
    "WrapperState",
    "InjectionProfile",
    "get_profile",
    "list_profile_ids",
    "CANONICAL_PROFILE_IDS",
    "apply_wrapper",
]
