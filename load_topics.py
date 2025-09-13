import json
import firebase_admin
from firebase_admin import credentials, firestore
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List

class TopicEntry(BaseModel):
    grade_level: str
    education_stage: str
    subject: str
    topic: str

class Topics(BaseModel):
    subjects: List[TopicEntry]

load_dotenv()
# --- Setup Firestore ---
cred = credentials.Certificate("dest-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Setup OpenAI ---
client = OpenAI()

education_map = {
    "primary": ["grade_1", "grade_2", "grade_3", "grade_4", "grade_5"],
    "middle": ["grade_6", "grade_7", "grade_8"],
    "high_school": ["grade_9", "grade_10", "grade_11", "grade_12"],
    "college_undergrad": ["year_1", "year_2", "year_3", "year_4"],
    "college_postgrad": ["year_1", "year_2"],
    "phd": ["research_phase"]
}

PROMPT_TEMPLATE = """
Generate an exhaustive list of subjects and their topics for:
Stage: {stage}, Grade: {grade}
Be exhaustive but concise. No explanations, JSON only.
"""

def generate_subjects(stage: str, grade: str) -> List[TopicEntry]:
    prompt = PROMPT_TEMPLATE.format(stage=stage, grade=grade)

    response = client.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format=Topics,
    )

    parsed = response.choices[0].message.parsed.model_dump()
    parsed = Topics(**parsed)
    print(parsed)
    return parsed.subjects

def store_in_firestore(stage, grade, subjects):
    batch = db.batch()
    for entry in subjects:
        subject = entry.subject
        topic=entry.topic
        if subject and topic:
            doc_id = f"{grade}_{subject}_{topic}".replace(" ", "_").lower()
            ref = db.collection("topics").document(doc_id)
            batch.set(ref, entry.model_dump())
    batch.commit()

import os

def save_to_json(stage, grade, subjects :List[TopicEntry], out_dir="subjects_json"):
    os.makedirs(out_dir, exist_ok=True)
    file_path = os.path.join(out_dir, f"{stage}_{grade}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump([subject.model_dump() for subject in subjects], f, indent=2, ensure_ascii=False)
    print(f"Saved JSON for {stage} - {grade} at {file_path}")


if __name__ == "__main__":
    for stage, grades in education_map.items():
        for grade in grades:
            print(f"Generating for {stage} - {grade}")
            subjects = generate_subjects(stage, grade)

            # Save for troubleshooting
            save_to_json(stage, grade, subjects)

            # Store in Firestore
            store_in_firestore(stage, grade, subjects)
