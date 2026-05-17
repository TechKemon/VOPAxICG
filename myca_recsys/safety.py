from __future__ import annotations

import re

from myca_recsys.models import Persona, SafetyInfo, UserProfile


CRISIS_PATTERNS = [
    ("suicide", r"\bsuicide\b"),
    ("suicidal", r"\bsuicidal\b"),
    ("self harm", r"\bself[-\s]?harm\b"),
    ("kill myself", r"\bkill myself\b"),
    ("end my life", r"\bend my life\b"),
    ("want to die", r"\bwant to die\b"),
    ("no reason to live", r"\bno reason to live\b"),
    ("crisis", r"\bcrisis\b"),
]

CRISIS_MESSAGE = (
    "This profile shows possible crisis signals. Please show immediate support resources "
    "and encourage the user to contact local emergency help or a trusted person now."
)


def detect_safety(profile: UserProfile | Persona, chat_history: str | None = None) -> SafetyInfo:
    text_parts = [
        *profile.feelings,
        *profile.challenges,
        *profile.goals,
        *profile.risk_signals,
        getattr(profile, "summary", ""),
        chat_history or "",
    ]
    combined = " ".join(text_parts).lower()
    matched = sorted(
        {
            label
            for label, pattern in CRISIS_PATTERNS
            if re.search(pattern, combined)
        }
    )
    return SafetyInfo(
        is_crisis=bool(matched),
        message=CRISIS_MESSAGE if matched else None,
        matched_signals=matched,
    )
