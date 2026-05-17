from __future__ import annotations

from myca_recsys.models import RecommendationRequest, UserProfile
from myca_recsys.service import RecommendationEngine


def run_recommendation(user_chat_history: str, profile: dict | None = None, top_n: int = 3):
    """
    Backward-compatible wrapper for the demo scripts.
    """
    request = RecommendationRequest(
        profile=UserProfile.model_validate(profile or {}),
        chat_history=user_chat_history,
        top_n=top_n,
    )
    response = RecommendationEngine().recommend(request)
    return _legacy_payload(response), format_final_message(response)


def format_final_message(response) -> str:
    persona = response.persona
    recommendations = response.recommendations

    if not recommendations:
        return "I analyzed your chat, but I couldn't find specific recommendations."

    feeling = persona.feelings[0] if persona.feelings else "concerned"
    challenge = persona.challenges[0] if persona.challenges else "what you are dealing with"

    msg = [
        f"You seem to be feeling **{feeling}** and dealing with **{challenge}**.",
    ]
    if response.safety.is_crisis and response.safety.message:
        msg.append(f"\n**Important:** {response.safety.message}")

    msg.extend(["\nHere are your top recommended courses:\n", "---"])
    for index, course in enumerate(recommendations, start=1):
        msg.append(f"**{index}. {course.title}**")
        msg.append(f"- **Why:** {course.reason}")
        msg.append(f"- **Score:** {course.score:.2f}\n---")
    return "\n".join(msg)


def _legacy_payload(response) -> dict:
    return {
        "generated_persona": {
            "summary": response.persona.summary,
            "expressed_feelings": response.persona.feelings,
            "reported_challenges": response.persona.challenges,
            "expressed_goals": response.persona.goals,
            "risk_signals": response.persona.risk_signals,
        },
        "recommendations": [
            {
                "id": item.id,
                "title": item.title,
                "score": item.score,
                "reason": item.reason,
                "matched_signals": item.matched_signals,
            }
            for item in response.recommendations
        ],
        "safety": response.safety.model_dump(),
        "model_metadata": response.model_metadata.model_dump(),
    }
