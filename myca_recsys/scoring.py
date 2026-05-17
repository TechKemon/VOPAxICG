from __future__ import annotations

import re
from dataclasses import dataclass

from myca_recsys.models import Course, Persona, RecommendationItem, ScoreBreakdown, SafetyInfo


TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class WeightedSignal:
    text: str
    weight: float


def rank_courses(courses: list[Course], persona: Persona, safety: SafetyInfo, top_n: int) -> list[RecommendationItem]:
    scored = [_score_course(course, persona, safety) for course in courses]
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:top_n]


def _score_course(course: Course, persona: Persona, safety: SafetyInfo) -> RecommendationItem:
    signals = _profile_signals(persona)
    course_text = _course_text(course)
    keyword_text = " ".join(course.keywords).lower()
    domain_text = " ".join(term for terms in course.domains.values() for term in terms).lower()

    matched: list[str] = []
    keyword_matches = 0
    domain_matches = 0
    text_matches = 0
    weighted_score = 0.0

    for signal in signals:
        if _matches(signal.text, keyword_text):
            keyword_matches += 1
            weighted_score += 3.0 * signal.weight
            matched.append(signal.text)
        if _matches(signal.text, domain_text):
            domain_matches += 1
            weighted_score += 2.0 * signal.weight
            matched.append(signal.text)
        if _matches(signal.text, course_text):
            text_matches += 1
            weighted_score += 1.0 * signal.weight
            matched.append(signal.text)

    penalty = _stopword_penalty(course, signals, matched)
    weighted_score = max(0.0, weighted_score - penalty)

    crisis_boost = 0.0
    if safety.is_crisis and course.id == "C006":
        crisis_boost = 8.0
        weighted_score += crisis_boost
        matched.extend(safety.matched_signals)

    normalized = min(weighted_score / 12.0, 1.0)
    unique_matches = sorted(set(matched))
    return RecommendationItem(
        id=course.id,
        title=course.title,
        score=round(normalized, 4),
        reason=_build_reason(course, persona, safety, unique_matches),
        matched_signals=unique_matches,
        scoring=ScoreBreakdown(
            keyword_matches=keyword_matches,
            domain_matches=domain_matches,
            text_matches=text_matches,
            stopword_penalty=round(penalty, 4),
            crisis_boost=crisis_boost,
        ),
    )


def _profile_signals(persona: Persona) -> list[WeightedSignal]:
    signals: list[WeightedSignal] = []
    signals.extend(WeightedSignal(item, 1.0) for item in persona.feelings)
    signals.extend(WeightedSignal(item, 1.3) for item in persona.challenges)
    signals.extend(WeightedSignal(item, 1.1) for item in persona.goals)
    signals.extend(WeightedSignal(item, 1.6) for item in persona.risk_signals)
    return [signal for signal in signals if signal.text.strip()]


def _course_text(course: Course) -> str:
    domain_terms = " ".join(term for terms in course.domains.values() for term in terms)
    return " ".join([course.title, course.description, " ".join(course.keywords), domain_terms]).lower()


def _matches(signal: str, target: str) -> bool:
    signal_tokens = _tokens(signal)
    if not signal_tokens:
        return False
    target_tokens = set(_tokens(target))
    if signal.lower() in target:
        return True
    overlap = signal_tokens & target_tokens
    return len(overlap) >= max(1, min(2, len(signal_tokens)))


def _tokens(text: str) -> set[str]:
    return {token for token in TOKEN_RE.findall(text.lower()) if len(token) > 2}


def _stopword_penalty(course: Course, signals: list[WeightedSignal], matched: list[str]) -> float:
    if not course.stopwords:
        return 0.0
    signal_text = " ".join(signal.text for signal in signals).lower()
    matched_text = " ".join(matched).lower()
    penalty = 0.0
    for stopword in course.stopwords:
        stopword_l = stopword.lower()
        if stopword_l in signal_text and stopword_l not in matched_text:
            penalty += 2.0
    return penalty


def _build_reason(course: Course, persona: Persona, safety: SafetyInfo, matched: list[str]) -> str:
    if safety.is_crisis and course.id == "C006":
        return "This is prioritized because the profile includes possible crisis or self-harm signals."
    if matched:
        visible = ", ".join(matched[:3])
        return f"This course matches the user's signals around {visible}."
    if persona.challenges:
        return f"This course may help with {persona.challenges[0]}."
    return "This course is a reasonable starting point for the user's current profile."
