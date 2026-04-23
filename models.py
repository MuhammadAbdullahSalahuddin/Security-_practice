from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Option:
    text: str
    is_correct: bool = False
    is_user_selected: bool = False  # Track what the scraper selected
    index: Optional[int] = None
    explanation: str = ""
    state: str = ""  # 'correct', 'incorrect', 'skipped'

@dataclass
class Question:
    question_number: str
    question_text: str
    question_type: str  # 'single_choice' or 'multiple_choice'
    
    # All options with their states
    all_options: List[Option] = field(default_factory=list)
    
    # Explicit categorization for clarity in JSON
    correct_answers: List[str] = field(default_factory=list)  # Text of correct options
    user_incorrect_answers: List[str] = field(default_factory=list)  # Text of wrong options user selected
    
    # Legacy fields (kept for compatibility)
    options: List[Option] = field(default_factory=list)  # Same as all_options
    correct_indices: List[int] = field(default_factory=list)
    
    explanation: str = ""
    screenshot_path: Optional[str] = None

@dataclass
class Exam:
    course_name: str
    exam_number: int
    questions: List[Question] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())