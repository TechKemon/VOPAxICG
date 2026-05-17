# app.py
import streamlit as st
import os
from recommendation import run_recommendation

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="MYCA: AI Student Advisor",
    page_icon="🎓",
    layout="centered"
)

# --- HEADER ---
st.title("🎓 MYCA: AI Course Advisor")
st.markdown("""
Welcome to the **MYCA Demo**. 
This system analyzes student chat history to detect **emotional state** and **challenges**, 
then recommends the best courses from our database.
""")

st.divider()

# --- SIDEBAR (Settings) ---
with st.sidebar:
    st.header("⚙️ Configuration")
    # Check if Token exists
    if os.getenv("HF_TOKEN"):
        st.success("HF_TOKEN found! ✅")
    else:
        st.error("HF_TOKEN is missing! ❌")
        st.info("Please set your API token in your environment variables.")
    
    st.markdown("---")
    st.caption("Powered by Qwen3.5-35B-A3B")

# --- MAIN INPUT ---
st.subheader("1. Input Student Conversation")
default_text = """I feel really overwhelmed with my current workload. 
I can't seem to focus on my assignments and I'm stressed about the upcoming exams.
I need something to help me manage my time better."""

user_input = st.text_area(
    "Paste chat history or notes here:", 
    value=default_text, 
    height=150
)

# --- ACTION BUTTON ---
if st.button("🚀 Analyze & Recommend", type="primary"):
    
    if not user_input.strip():
        st.warning("Please enter some text first.")
    else:
        with st.spinner("Analyzing student persona and searching database..."):
            try:
                # CALL YOUR EXISTING FUNCTION
                # We only need the raw data to display it prettily here, 
                # but we can also show the text string if we want.
                data, final_message_str = run_recommendation(user_input)
                
                # --- RESULTS AREA ---
                st.success("Analysis Complete!")
                
                # 1. Display Persona (The "Why")
                st.subheader("2. Student Persona Analysis")
                col1, col2 = st.columns(2)
                
                persona = data.get("generated_persona", {})
                
                with col1:
                    st.info(f"**Detected Feeling:**\n {persona.get('expressed_feelings', ['Unknown'])[0]}")
                with col2:
                    st.warning(f"**Main Challenge:**\n {persona.get('reported_challenges', ['Unknown'])[0]}")
                
                # 2. Display Recommendations (The "What")
                st.subheader("3. Recommended Courses")
                
                reccs = data.get("recommendations", [])
                
                for idx, rec in enumerate(reccs):
                    with st.expander(f"#{idx+1}: {rec['title']}", expanded=True):
                        st.markdown(f"**Why this fits:** {rec['reason']}")
                        
                
                # 3. Show the "Chatbot" Response Style
                with st.expander("👀 View Chatbot Response Output"):
                    st.markdown(final_message_str)
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")