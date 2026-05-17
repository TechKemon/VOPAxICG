from __future__ import annotations

import os

import streamlit as st

from myca_recsys.config import load_settings
from myca_recsys.models import RecommendationRequest, UserProfile
from myca_recsys.service import RecommendationEngine
from recommendation import format_final_message


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


st.set_page_config(page_title="MYCA Course Recommender", page_icon="MYCA", layout="centered")

st.title("MYCA Course Recommender")
st.markdown(
    "Paste a MYCA conversation and optional profile signals. The app extracts the persona, "
    "ranks courses deterministically, and flags crisis signals."
)

settings = load_settings()
with st.sidebar:
    st.header("Configuration")
    st.caption(f"Persona model: {settings.hf_model_id}")
    if os.getenv("HF_TOKEN"):
        st.success("HF_TOKEN found")
    else:
        st.warning("HF_TOKEN missing; profile/chat fallback will be used.")

default_text = """I feel overwhelmed about exams and I keep comparing myself with classmates.
My parents expect a lot from me and I am scared I will disappoint them."""

chat_history = st.text_area("MYCA conversation", value=default_text, height=180)
feelings = st.text_input("Feelings", value="scared, overwhelmed")
challenges = st.text_input("Challenges", value="exam pressure, family expectations")
goals = st.text_input("Goals", value="manage stress")
top_n = st.slider("Number of courses", min_value=1, max_value=8, value=3)

if st.button("Analyze and recommend", type="primary"):
    try:
        request = RecommendationRequest(
            profile=UserProfile(
                feelings=_split_csv(feelings),
                challenges=_split_csv(challenges),
                goals=_split_csv(goals),
            ),
            chat_history=chat_history,
            top_n=top_n,
        )
        response = RecommendationEngine().recommend(request)
    except Exception as exc:
        st.error(f"Could not create recommendations: {exc}")
    else:
        if response.safety.is_crisis and response.safety.message:
            st.error(response.safety.message)

        st.subheader("Persona")
        st.write(response.persona.summary)
        cols = st.columns(3)
        cols[0].metric("Feelings", len(response.persona.feelings))
        cols[1].metric("Challenges", len(response.persona.challenges))
        cols[2].metric("Goals", len(response.persona.goals))

        st.subheader("Recommended courses")
        for item in response.recommendations:
            with st.expander(f"{item.id}: {item.title} ({item.score:.2f})", expanded=True):
                st.write(item.reason)
                st.caption("Matched signals: " + (", ".join(item.matched_signals) or "none"))

        with st.expander("Chatbot response"):
            st.markdown(format_final_message(response))
