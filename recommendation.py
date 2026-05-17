import os
import json
import requests
import sys
from pathlib import Path
from dotenv import load_dotenv

# -----------------------------------------------------------
# 1. SETUP & AUTHENTICATION (The Fix)
# -----------------------------------------------------------

current_file_path = Path(__file__).resolve()
project_folder = current_file_path.parent
env_path = project_folder / ".env"

# Load environment variables (Silent mode)
load_dotenv(dotenv_path=env_path, override=True) 

# Get & Clean Token
raw_token = os.getenv("HF_TOKEN")
if raw_token:
    HF_TOKEN = raw_token.strip().replace('"', '').replace("'", "")
else:
    HF_TOKEN = None
    # We only print errors, not success messages
    print("❌ CRITICAL ERROR: HF_TOKEN is missing.")

# Fix Import Path for course_list.py
if str(project_folder) not in sys.path:
    sys.path.append(str(project_folder))

try:
    from course_list import course_list
except ImportError:
    course_list = []
def run_recommendation(user_chat_history: str):
    """
    Takes user chat text and returns:
    - raw JSON response from model (persona + recommendations)
    - formatted chatbot message
    """

    # 1. Safety Check
    if not HF_TOKEN:
        return None, "System Error: API Token is missing. Please check .env file."

    # 2. Setup API
    API_URL = "https://router.huggingface.co/v1/chat/completions"
    MODEL_ID = "Qwen/Qwen3.5-35B-A3B"

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    # 3. Create Prompts
    system_prompt = """You are an expert student advisor and psychological analyst. 
    Your job is to perform two tasks:
    1. Analyze a user's raw chat history to generate a structured `persona`.
    2. Use that generated persona to rank a provided `course_list` and select the top 3 recommendations.

    You MUST respond with ONLY a valid JSON object following this exact schema:
    {
      "generated_persona": {
        "summary": "A brief summary...",
        "expressed_feelings": ["feeling1", "feeling2"],
        "reported_challenges": ["challenge1", "challenge2"],
        "expressed_goals": ["goal1", "goal2"]
      },
      "recommendations": [
        {"id": "...", "title": "...", "reason": "..."},
        {"id": "...", "title": "...", "reason": "..."},
        {"id": "...", "title": "...", "reason": "..."}
      ]
    }
    """

    user_prompt = f"""
    <user_chat>
    {user_chat_history}
    </user_chat>

    <course_list>
    {json.dumps(course_list)}
    </course_list>
    """

    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.1,
        "chat_template_kwargs": {"enable_thinking": False},  # disables think block
        "response_format": {"type": "json_object"},
        "stream": False
    }

    # 4. Call API
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        # If this fails with 401, it will print the specific error reason
        if response.status_code == 401:
            print(f"❌ API AUTH ERROR: {response.text}")
            return None, "Error: Authentication failed. Check API Key."
            
        response.raise_for_status()

        # 5. Parse Response
        content = response.json()["choices"][0]["message"]["content"]

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
        
        data = json.loads(content)
        final_message = format_final_message(data)

        return data, final_message

    except Exception as e:
        print(f"❌ EXECUTION ERROR: {str(e)}")
        return None, f"An error occurred: {str(e)}"


# -----------------------------------------------------------
# 3. HELPER: FORMAT OUTPUT
# -----------------------------------------------------------
def format_final_message(api_response_data):
    try:
        persona = api_response_data.get("generated_persona", {})
        reccs = api_response_data.get("recommendations", [])

        if not reccs:
            return "I analyzed your chat, but I couldn't find specific recommendations."

        feeling = persona.get("expressed_feelings", ["concerned"])[0]
        challenge = persona.get("reported_challenges", ["workload"])[0]

        msg = [
            f"You seem to be feeling **{feeling}** and struggling with **{challenge}**.",
            "\nHere are your top 3 recommended courses:\n",
            "---"
        ]

        for i, c in enumerate(reccs):
            msg.append(f"**{i+1}. {c.get('title', 'Course')}**")
            msg.append(f"- **Why:** {c.get('reason', 'N/A')}\n---")

        return "\n".join(msg)

    except Exception:
        return "Error generating the final chat message."