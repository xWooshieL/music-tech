"""Per-piece tuning profile for :class:`HybridScoreFollower`.

The hybrid follower exposes ~30 hyperparameters (confidence threshold,
anchor-window lengths, debounce widths, etc.). Tuning them globally
does not work: different pieces have very different note densities
and tempo behavior. We therefore keep a JSON profile next to each
``score.json`` file (``<piece>.hybrid_profile.json``) with overrides
for the hybrid follower constructor.

A profile is a flat ``{key: value}`` mapping. Unknown keys are
silently ignored, which lets calibrators add new tuning knobs without
breaking older profiles. The list of accepted keys lives in
:data:`HYBRID_PROFILE_TUNING_KEYS`.

This module is intentionally tiny: it only knows how to find and load
profiles. Profile *writing* is done by
``calibrate_hybrid_profile.py`` and friends and uses these same keys.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "HYBRID_PROFILE_FORMAT_VERSION",
    "HYBRID_PROFILE_TUNING_KEYS",
    "hybrid_profile_path",
    "load_hybrid_profile",
]


HYBRID_PROFILE_TUNING_KEYS = frozenset(
    {
        "confidence_threshold",
        "resync_gap",
        "nudge_target_mass",
        "sigma",
        "outlier_pitch_clip",
        "max_local_cost",
        "max_forward_match_gap",
        "max_forward_match_lead_over_oltw",
        "max_forward_step",
        "recovery_confirmation_events",
        "anchor_window_lengths",
        "anchor_pitch_clip",
        "anchor_total_cost_threshold",
        "anchor_margin_threshold",
        "anchor_time_weight",
        "anchor_min_tempo_scale",
        "anchor_max_tempo_scale",
        "anchor_local_improvement_threshold",
        "anchor_search_max_events",
        "anchor_confirmation_events",
        "anchor_stability_tolerance",
        "anchor_min_jump",
        "anchor_min_supporting_windows",
        "anchor_local_preference_margin",
        "output_confirmation_events",
        "output_high_confidence",
    }
)

HYBRID_PROFILE_FORMAT_VERSION = 2


def hybrid_profile_path(score_json_path: str | Path) -> Path:
    """Return ``<score>.hybrid_profile.json`` next to a given score file."""
    score_path = Path(score_json_path)
    return score_path.with_suffix(".hybrid_profile.json")


def load_hybrid_profile(
    score_json: str | Path | dict[str, Any] | list[dict[str, Any]],
) -> tuple[dict[str, Any], Path | None]:
    """Load a hybrid-follower tuning profile for ``score_json``.

    Returns a pair ``(overrides, profile_path)``. ``overrides`` is the
    dictionary of accepted keys (anything outside
    :data:`HYBRID_PROFILE_TUNING_KEYS` is dropped). ``profile_path`` is
    the expected location of the profile file, or ``None`` when the
    input is not file-backed (e.g. an in-memory dict was passed).

    The function never raises: missing, malformed, or version-mismatched
    profiles all collapse to an empty ``overrides`` dictionary.
    """
    if not isinstance(score_json, (str, Path)):
        return {}, None

    score_path = Path(score_json)
    if score_path.suffix.lower() != ".json":
        return {}, None

    profile_path = hybrid_profile_path(score_path)
    if not profile_path.exists():
        return {}, profile_path

    try:
        payload = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}, profile_path

    format_version = payload.get("format_version")
    if format_version != HYBRID_PROFILE_FORMAT_VERSION:
        return {}, profile_path

    tuning = payload.get("tuning", payload)
    if not isinstance(tuning, dict):
        return {}, profile_path

    overrides = {
        key: value for key, value in tuning.items() if key in HYBRID_PROFILE_TUNING_KEYS
    }
    if "anchor_window_lengths" in overrides:
        try:
            overrides["anchor_window_lengths"] = tuple(
                int(length) for length in overrides["anchor_window_lengths"]
            )
        except (TypeError, ValueError):
            overrides.pop("anchor_window_lengths", None)

    return overrides, profile_path
