from dotenv import load_dotenv
from firebase_admin import credentials, firestore
import firebase_admin


load_dotenv()
# --- Setup Firestore ---
cred = credentials.Certificate("dest-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


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
