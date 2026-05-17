from myca_recsys.catalog import load_courses
from myca_recsys.models import Persona
from myca_recsys.safety import detect_safety
from myca_recsys.scoring import rank_courses


def test_youth_pressure_profile_ranks_youth_course_first():
    persona = Persona(
        feelings=["scared"],
        challenges=["exam pressure", "fear of failure", "career stress"],
        goals=["manage stress"],
    )

    ranked = rank_courses(load_courses(), persona, detect_safety(persona), top_n=3)

    assert ranked[0].id == "C008"
    assert "fear of failure" in ranked[0].matched_signals


def test_crisis_profile_boosts_suicide_prevention_course():
    persona = Persona(
        feelings=["hopeless"],
        challenges=["I want to die"],
        risk_signals=["self harm"],
    )
    safety = detect_safety(persona)

    ranked = rank_courses(load_courses(), persona, safety, top_n=3)

    assert safety.is_crisis is True
    assert safety.matched_signals == ["self harm", "want to die"]
    assert ranked[0].id == "C006"
    assert ranked[0].scoring.crisis_boost > 0


def test_stopword_penalty_does_not_block_direct_match():
    persona = Persona(challenges=["sexual health"])

    ranked = rank_courses(load_courses(), persona, detect_safety(persona), top_n=3)

    assert ranked[0].id == "C004"


def test_suicide_prevention_is_not_tie_boosted_without_crisis():
    persona = Persona(challenges=["fear of failure"])

    ranked = rank_courses(load_courses(), persona, detect_safety(persona), top_n=3)

    assert ranked[0].id == "C008"
    assert ranked[1].id != "C006"
