from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List
import re
import os
from fastapi.middleware.cors import CORSMiddleware

def extract_qnum(raw) -> int:
    """Handles 'Question 1', '1', 1, etc."""
    if isinstance(raw, int):
        return raw
    m = re.search(r'\d+', str(raw))
    return int(m.group()) if m else 0

app = FastAPI(title="Security+ Practice API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to the local MongoDB container mapped to 27017
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client["security_practice"]
exams_collection = db["exams"]

# Pydantic models for incoming data validation
class UserAnswer(BaseModel):
    question_number: int
    selected_indices: List[int]

class GradingRequest(BaseModel):
    practice_set: str
    exam_id: str
    user_answers: List[UserAnswer]

@app.get("/")
def health_check():
    return {"status": "Active", "service": "Security+ API"}

@app.get("/api/v1/exams")
def list_available_exams():
    """Returns a list of all practice sets and their associated exams."""
    pipeline = [
        {"$group": {"_id": "$practice_set", "exams": {"$push": "$exam_id"}}},
        {"$sort": {"_id": 1}}
    ]
    results = list(exams_collection.aggregate(pipeline))
    return {"data": results}

@app.get("/api/v1/exams/{practice_set}/{exam_id}")
def get_exam(practice_set: str, exam_id: str):
    exam = exams_collection.find_one(
        {"practice_set": practice_set, "exam_id": exam_id},
        {"_id": 0, "questions.correct_indices": 0}  # only hide answers, keep explanation
    )
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam

@app.post("/api/v1/grade")
def grade_exam(payload: GradingRequest):
    exam = exams_collection.find_one({"practice_set": payload.practice_set, "exam_id": payload.exam_id})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    score = 0
    results = []

    correct_lookup = {
    int(str(q["question_number"]).replace("Question ", "").strip()): 
        q.get("correct_indices") or q.get("additional_information", {}).get("correct_indices", [])
    for q in exam["questions"]
}

    question_lookup = {
        extract_qnum(q["question_number"]): q
        for q in exam["questions"]
    }

    for answer in payload.user_answers:
        qnum = extract_qnum(answer.question_number)
        actual_correct = correct_lookup.get(qnum, [])
        is_correct = sorted(answer.selected_indices) == sorted(actual_correct)

        if is_correct:
            score += 1

        q = question_lookup.get(qnum, {})
        results.append({
            "question_number": qnum,
            "is_correct": is_correct,
            "correct_indices": actual_correct,
            "explanation": q.get("explanation") or q.get("additional_information", {}).get("explanation", ""),
        })

    total = len(exam["questions"])

    return {
        "total_questions": total,
        "score": score,
        "percentage": round((score / total) * 100, 2) if total else 0,
        "details": results
    }

