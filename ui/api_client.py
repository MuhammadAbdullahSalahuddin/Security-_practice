import requests
import re
import streamlit as st
from typing import Optional, Dict, List

API_BASE_URL = "http://127.0.0.1:8000/api/v1"

def parse_question_number(raw) -> int:
    """Convert any question_number representation to int."""
    if isinstance(raw, int):
        return raw
    m = re.search(r'\d+', str(raw))
    return int(m.group()) if m else 0

class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url

    def get_exams(self) -> List[Dict]:
        try:
            r = requests.get(f"{self.base_url}/exams", timeout=5)
            return r.json().get("data", [])
        except requests.exceptions.ConnectionError:
            st.error("⚠ Cannot reach API. Make sure the FastAPI backend is running on port 8000.")
            return []

    def get_exam(self, practice_set: str, exam_id: str) -> Optional[Dict]:
        try:
            r = requests.get(f"{self.base_url}/exams/{practice_set}/{exam_id}", timeout=5)
            if r.status_code == 200:
                return r.json()
            st.error(f"Exam not found ({r.status_code})")
            return None
        except Exception as e:
            st.error(f"API error: {e}")
            return None

    def grade_exam(self, practice_set: str, exam_id: str, answers: Dict) -> Optional[Dict]:
        user_answers = []
        for q_num, indices in answers.items():
            user_answers.append({
                "question_number": parse_question_number(q_num),
                "selected_indices": indices if indices else [],
            })

        payload = {
            "practice_set": practice_set,
            "exam_id": exam_id,
            "user_answers": user_answers,
        }
        try:
            r = requests.post(f"{self.base_url}/grade", json=payload, timeout=10)
            if r.status_code == 200:
                return r.json()
            st.error(f"Grading failed ({r.status_code}): {r.text}")
            return None
        except Exception as e:
            st.error(f"Grading error: {e}")
            return None