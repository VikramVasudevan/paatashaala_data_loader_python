import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from typing import List, Dict
from pydantic import BaseModel

# ---------- MODELS ----------
class TopicEntry(BaseModel):
    grade_level: str  # string key like "primary_1"
    education_stage: str
    subject: str
    topic: str

# ---------- HELPERS ----------
def load_topic_entries_from_folder(folder: str) -> List[TopicEntry]:
    entries: List[TopicEntry] = []
    for file in os.listdir(folder):
        if not file.endswith(".json"):
            continue
        with open(os.path.join(folder, file), "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                entries.append(TopicEntry(**item))
    return entries

def format_grade_label(stage: str, grade: str) -> str:
    stage_label = stage.replace("_", " ").title()
    grade_label = grade.replace("_", " ").title()
    return f"{stage_label} - {grade_label}"

# Mapping stage+grade string → integer level
GRADE_ORDER = {
    "primary": 1,
    "middle": 2,
    "high_school": 3,
    "college": 4,
    "college_undergrad": 5,
    "college_postgrad": 6,
    "phd": 7,
}

def extract_grades(topics: List[TopicEntry]) -> List[Dict]:
    seen = set()
    grade_entries = []

    for t in topics:
        key = (t.education_stage, t.grade_level)
        if key not in seen:
            seen.add(key)

            # compute integer grade level
            stage_base = GRADE_ORDER.get(t.education_stage.lower(), 0)
            number_part = 0
            for c in t.grade_level:
                if c.isdigit():
                    number_part = int(c)
                    break

            # Combine for sortable integer
            int_grade_level = stage_base * 100 + number_part

            grade_entries.append({
                "education_stage": t.education_stage,
                "grade_key": t.grade_level,       # string key
                "grade_level": int_grade_level,   # integer level
                "grade_label": format_grade_label(t.education_stage, t.grade_level),
            })
    return grade_entries

# ---------- FIRESTORE ----------
def batch_insert_grades(grades: List[Dict], collection: str = "grades"):
    cred = credentials.Certificate("dest-key.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    batch = db.batch()

    for grade in grades:
        doc_ref = db.collection(collection).document(f"{grade['education_stage']}_{grade['grade_key']}")
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
