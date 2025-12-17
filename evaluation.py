import pandas as pd
import sys
import os
from pathlib import Path

# --- 1. DYNAMIC PATH SETUP ---
# This finds the folder where THIS file lives
project_folder = Path(__file__).resolve().parent

# Make sure Python can find 'recommendation.py' in this folder
if str(project_folder) not in sys.path:
    sys.path.append(str(project_folder))

from recommendation import run_recommendation

def run_evaluation():
    # --- 2. DEFINE FILE PATHS AUTOMATICALLY ---
    # Look for the input file inside the project folder
    input_csv = project_folder / "myca_eval_dataset.csv"
    output_csv = project_folder / "myca_new_dataset.csv"

    print(f"📂 Project Folder: {project_folder}")
    print(f"🔍 Looking for input file at: {input_csv}")

    # --- 3. SAFETY CHECK ---
    if not input_csv.exists():
        print("\n❌ ERROR: Input file not found!")
        print(f"Please move 'myca_eval_dataset.csv' into this folder: {project_folder}")
        return

    print("✅ File found! Starting evaluation...")

    # --- 4. RUN EVALUATION ---
    try:
        df = pd.read_csv(input_csv)
        
        results = []
        messages = []

        # Loop through each row
        print(f"⏳ Processing {len(df)} rows...")
        for idx, row in df.iterrows():
            # Combine context and conversation safely
            context = str(row.get("context", ""))
            conversation = str(row.get("conversation", ""))
            text = f"{context}\n{conversation}"

            # Run your AI Logic
            # We use a try-except here so one bad row doesn't crash the whole script
            try:
                data, final_msg = run_recommendation(text)
                
                # Extract recommendations list safely
                recs = data.get("recommendations", []) if data else []
                results.append(recs)
                messages.append(final_msg)
                
                # Optional: Print a dot for every row processed so you know it's working
                print(".", end="", flush=True)

            except Exception as e:
                print(f"⚠️ Error on row {idx}: {e}")
                results.append([])
                messages.append("Error processing this row.")

        print("\n✅ Processing complete.")

        # Save Results
        df["model_recommendations"] = results
        df["model_message"] = messages

        df.to_csv(output_csv, index=False)
        print(f"🎉 Success! Results saved to: {output_csv}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")

if __name__ == "__main__":
    run_evaluation()