from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Security+ Practice API")

# Connect to the local MongoDB container mapped to 27017
client = MongoClient("mongodb://localhost:27017/")
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
    """Fetches a specific exam without the correct answers to prevent cheating."""
    exam = exams_collection.find_one(
        {"practice_set": practice_set, "exam_id": exam_id},
        {"_id": 0} 
    )
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam

@app.post("/api/v1/grade")
def grade_exam(payload: GradingRequest):
    """Evaluates the user's submissions against the database."""
    exam = exams_collection.find_one({"practice_set": payload.practice_set, "exam_id": payload.exam_id})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    score = 0
    results = []
    
    # Create a quick lookup dictionary for correct answers
    correct_lookup = {q["question_number"]: q["correct_indices"] for q in exam["questions"]}
    
    for answer in payload.user_answers:
        actual_correct = correct_lookup.get(answer.question_number, [])
        is_correct = sorted(answer.selected_indices) == sorted(actual_correct)
        
        if is_correct:
            score += 1
            
        results.append({
            "question_number": answer.question_number,
            "is_correct": is_correct,
            "correct_indices": actual_correct,
            "explanation": next((q["explanation"] for q in exam["questions"] if q["question_number"] == answer.question_number), "")
        })
        
    return {
        "total_questions": len(exam["questions"]),
        "score": score,
        "percentage": round((score / len(exam["questions"])) * 100, 2),
        "details": results
    }