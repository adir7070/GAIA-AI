"""Diversity matrix for synthetic personas.

We sample style traits from independent axes so the dataset doesn't collapse to
a single average style (per spec §10 + lecturer feedback in gpt.md about
'style collapse').
"""
from __future__ import annotations

import random

LANGUAGES = ["he", "en"]
LENGTHS = ["very_short", "short", "medium", "long"]
EMOJIS = ["none", "sparse", "frequent", "heavy"]
SLANG = ["none", "some", "heavy"]
FORMALITY = ["very_casual", "casual", "neutral", "formal"]
RHYTHM = ["single", "multi", "mixed"]
PUNCT_STYLES = [
    "minimal punctuation, lowercase only",
    "standard punctuation",
    "lots of !!! and ???",
    "ellipses everywhere...",
    "no end punctuation",
]
GREETINGS = [
    "abrupt, no greeting",
    "warm hi/hello most of the time",
    "always uses a name or nickname",
    "starts with an emoji often",
]
OCCUPATIONS = [
    "student",
    "software engineer",
    "designer",
    "teacher",
    "doctor",
    "small business owner",
    "marketing manager",
    "freelancer",
    "investor",
    "consultant",
]
AGE_BUCKETS = ["18-24", "25-34", "35-44", "45-54", "55+"]


def sample_seed(rng: random.Random, user_id: str) -> dict:
    return {
        "user_id": user_id,
        "language": rng.choice(LANGUAGES),
        "avg_length": rng.choice(LENGTHS),
        "emoji": rng.choice(EMOJIS),
        "slang": rng.choice(SLANG),
        "formality": rng.choice(FORMALITY),
        "rhythm": rng.choice(RHYTHM),
        "punctuation": rng.choice(PUNCT_STYLES),
        "greeting_habits": rng.choice(GREETINGS),
        "occupation": rng.choice(OCCUPATIONS),
        "age_bucket": rng.choice(AGE_BUCKETS),
    }
