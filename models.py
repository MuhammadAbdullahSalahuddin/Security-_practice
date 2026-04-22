from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Option:
    text: str
    is_correct: bool = False
    index: Optional[int] = None
    explanation: str = ""

@dataclass
class Question:
    question_number: str
    question_text: str
    question_type: str  # 'single_choice' or 'multiple_choice'
    options: List[Option] = field(default_factory=list)
    correct_indices: List[int] = field(default_factory=list)
    explanation: str = ""
    screenshot_path: Optional[str] = None

@dataclass
class Exam:
    course_name: str
    exam_number: int
    questions: List[Question] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
