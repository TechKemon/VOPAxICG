from myca_recsys.models import RecommendationRequest, UserProfile
from myca_recsys.service import RecommendationEngine

def main():
    user_text = "I feel stressed at work, my sleep is getting worse, and I need help with burnout."
    profile = UserProfile(feelings=["stressed"], challenges=["burnout", "poor sleep"], goals=["feel calmer"])

    response = RecommendationEngine().recommend(
        RecommendationRequest(profile=profile, chat_history=user_text, top_n=3)
    )

    print("\n--- RESPONSE JSON ---")
    print(response.model_dump_json(indent=2))

    print("\n--- TOP COURSES ---")
    for item in response.recommendations:
        print(f"{item.id} | {item.title} | score={item.score:.2f} | {item.reason}")


if __name__ == "__main__":
    main()
