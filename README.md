```markdown
# VOPAxICG: AI Student Advisor & Course Recommender

This project is an AI-powered student advisor system that analyzes a user's chat history to detect emotional states (stress, anxiety) and challenges (workload, time management). Based on this analysis, it generates a psychological "persona" and recommends the top 3 most relevant courses from a database using the **Qwen3.5-35B-A3B** LLM via Hugging Face.

## 📂 Project Structure

```text
VOPAxICG/
├── course_list.py       # Database of available courses (JSON format)
├── main.py              # Entry point for backend testing (CLI)
├── recommendation.py    # Core logic (API communication & Prompt Engineering)
├── evaluation.py        # Scripts for batch testing and metrics
├── Demo_app.py          # Streamlit Web Application (Frontend)
├── requirements.txt     # List of python dependencies
├── .env                 # (Ignored by Git) Stores your API Key safely
└── .gitignore           # Specifies files to exclude from git

```

## 🚀 Installation & Setup

### 1. Prerequisites

* **Python 3.8** or higher.
* A **Hugging Face Account** & **API Token** ([Get one here](https://huggingface.co/settings/tokens)).

### 2. Clone the Repository

```bash
git clone [https://github.com/ic1ic2/VOPAxICG.git](https://github.com/ic1ic2/VOPAxICG.git)
cd VOPAxICG

```

### 3. Create & Activate Virtual Environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate

```

**Mac / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate

```

### 4. Install Dependencies

```bash
pip install -r requirements.txt

```

### 5. Setup API Keys (Important!)

You must create a `.env` file to store your Hugging Face token.
**Run this specific command** in your terminal to create the file correctly (avoids Windows encoding errors):

*(Replace `hf_YOUR_ACTUAL_TOKEN` with your real key)*

```bash
python -c "with open('.env', 'w', encoding='utf-8') as f: f.write('HF_TOKEN=hf_YOUR_ACTUAL_TOKEN')"

```

---

## 🖥️ Usage

### Option A: Run the Web App (Recommended)

Launch the interactive dashboard to chat with the AI advisor.

```bash
streamlit run Demo_app.py

```

* The app will open automatically in your browser.
* **To Stop:** Press `Ctrl + C` in the terminal.

### Option B: Run Backend Test

Test the recommendation logic directly in the terminal without the UI.

```bash
python main.py

```

### Option C: Run Evaluation

Run the batch processing script to evaluate performance on multiple user personas.

```bash
python evaluation.py

```
