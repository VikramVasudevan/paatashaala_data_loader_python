import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from typing import List, Dict
from pydantic import BaseModel

# ---------- MODELS ----------
class TopicEntry(BaseModel):
    grade_level: str
    education_stage: str
    subject: str
    topic: str

# ---------- HELPERS ----------
def load_topic_entries_from_folder(folder: str) -> List[TopicEntry]:
    """
    Load all JSON files from subjects_json/ and parse into TopicEntry list.
    """
    entries: List[TopicEntry] = []
    for file in os.listdir(folder):
        if not file.endswith(".json"):
            continue
        with open(os.path.join(folder, file), "r", encoding="utf-8") as f:
            data = json.load(f)
            # Expecting a list of dicts (flat entries)
            for item in data:
                entries.append(TopicEntry(**item))
    return entries

def format_grade_label(stage: str, grade: str) -> str:
    stage_label = stage.replace("_", " ").title()
    grade_label = grade.replace("_", " ").title()
    return f"{stage_label} - {grade_label}"

def extract_grades(topics: List[TopicEntry]) -> List[Dict]:
    seen = set()
    grade_entries = []
    for t in topics:
        key = (t.education_stage, t.grade_level)
        if key not in seen:
            seen.add(key)
            grade_entries.append({
                "education_stage": t.education_stage,
                "grade_level": t.grade_level,
                "label": format_grade_label(t.education_stage, t.grade_level),
            })
    return grade_entries

# ---------- FIRESTORE ----------
def batch_insert_grades(grades: List[Dict], collection: str = "grades"):
    # --- Setup Firestore ---
    cred = credentials.Certificate("dest-key.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    batch = db.batch()

    for grade in grades:
        doc_ref = db.collection(collection).document(f"{grade['education_stage']}_{grade['grade_level']}")
        batch.set(doc_ref, grade)

    batch.commit()
    print(f"✅ Inserted {len(grades)} grades into '{collection}' collection.")

# ---------- PIPELINE ----------
def main():
    folder = "subjects_json"
    topics = load_topic_entries_from_folder(folder)
    print(f"Loaded {len(topics)} topic entries from {folder}/")

    grades = extract_grades(topics)
    print(f"Extracted {len(grades)} unique grades")

    batch_insert_grades(grades)

if __name__ == "__main__":
    main()
