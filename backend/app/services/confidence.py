"""Heuristic confidence: combines retrieval similarity and surface stats.

This is the v1 approach mentioned in the spec (§21). Once we have a fine-tuned
model with logprobs, we replace this with token-level uncertainty.
"""
from __future__ import annotations

from typing import Literal


Label = Literal["ANSWER_NOW", "ASK_USER_FOR_TEACHING", "UNSURE"]


def score_confidence(*, suggestion: str, similar: list[dict]) -> tuple[float, Label]:
    if not suggestion or not suggestion.strip():
        return 0.0, "ASK_USER_FOR_TEACHING"

    top_score = max((s.get("score", 0.0) for s in similar), default=0.0)
    avg_score = sum((s.get("score", 0.0) for s in similar)) / max(1, len(similar))

    # combine: top match weight + breadth weight
    confidence = 0.65 * top_score + 0.35 * avg_score
    confidence = max(0.0, min(1.0, confidence))

    if confidence >= 0.75:
        label: Label = "ANSWER_NOW"
    elif confidence >= 0.5:
        label = "UNSURE"
    else:
        label = "ASK_USER_FOR_TEACHING"
    return round(confidence, 3), label
