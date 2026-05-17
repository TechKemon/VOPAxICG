# VOPAxICG: MYCA Hybrid Course Recommender

This project recommends MYCA mental-health courses from a user profile and optional chat history. It now uses a hybrid design: the LLM can enrich the persona, but deterministic scoring owns the final course ranking so results are easier to test, debug, and trust.

## What It Provides

- `POST /v1/recommendations` for production integration.
- `GET /v1/courses` for the current course catalog.
- `GET /health` for service readiness.
- A Streamlit demo in `Demo_app.py`.
- A CLI smoke test in `main.py`.
- An evaluation script that compares predicted course ids with `myca_eval_dataset.csv`.

## Recommendation Flow

1. MYCA sends a structured profile and optional chat history.
2. If `HF_TOKEN` is available, the Hugging Face model extracts or enriches the persona.
3. If the model fails or no token is configured, the system falls back to the supplied profile and chat summary.
4. The deterministic ranker scores courses using keywords, descriptions, domain terms, stopwords, and safety signals.
5. Crisis or self-harm signals trigger a safety flag and boost the suicide-prevention course while still returning recommendations.

## API Example

```bash
curl -X POST http://localhost:8000/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "feelings": ["anxious"],
      "challenges": ["exam pressure", "fear of failure"],
      "goals": ["manage stress"],
      "risk_signals": []
    },
    "chat_history": "I am scared about exams and marks.",
    "top_n": 3
  }'
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` if you want LLM persona enrichment:

```bash
HF_TOKEN=hf_your_token
HF_MODEL_ID=Qwen/Qwen3.5-35B-A3B
```

The system still works without `HF_TOKEN`; it simply uses the profile/chat fallback.

## Run

```bash
uvicorn myca_recsys.api:app --reload
```

```bash
streamlit run Demo_app.py
```

```bash
python main.py
```

```bash
python evaluation.py
```

## Test

```bash
pytest
```
