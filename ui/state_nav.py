import streamlit as st
import time
from typing import Optional, Dict, List, Any

EXAM_DURATION_SECONDS = 7200

class ExamState:
    """Wraps st.session_state with typed accessors."""
    
    DEFAULTS: Dict[str, Any] = {
        "page": "welcome",          
        "mode": None,               
        "practice_set": None,
        "exam_id": None,
        "exam_data": None,
        "answers": {},              
        "submitted_qs": set(),      
        "results": None,
        "end_time": None,
        "focus_q": None,            
    }

    def __init__(self):
        for k, v in self.DEFAULTS.items():
            if k not in st.session_state:
                st.session_state[k] = v

    def reset(self):
        for k, v in self.DEFAULTS.items():
            st.session_state[k] = v

    @property
    def page(self) -> str: return st.session_state.page
    @page.setter
    def page(self, v: str): st.session_state.page = v

    @property
    def mode(self) -> Optional[str]: return st.session_state.mode
    @mode.setter
    def mode(self, v: str): st.session_state.mode = v

    @property
    def exam_data(self) -> Optional[Dict]: return st.session_state.exam_data
    @exam_data.setter
    def exam_data(self, v): st.session_state.exam_data = v

    @property
    def answers(self) -> Dict: return st.session_state.answers

    @property
    def submitted_qs(self) -> set: return st.session_state.submitted_qs

    @property
    def results(self): return st.session_state.results
    @results.setter
    def results(self, v): st.session_state.results = v

    @property
    def end_time(self) -> Optional[float]: return st.session_state.end_time
    @end_time.setter
    def end_time(self, v): st.session_state.end_time = v

    @property
    def focus_q(self): return st.session_state.focus_q
    @focus_q.setter
    def focus_q(self, v): st.session_state.focus_q = v

    @property
    def time_expired(self) -> bool:
        if self.mode != "exam" or not self.end_time:
            return False
        return time.time() > self.end_time

    def set_answer(self, q_num, indices: List[int]):
        st.session_state.answers[q_num] = indices

    def lock_question(self, q_num):
        st.session_state.submitted_qs.add(q_num)

    def is_locked(self, q_num) -> bool:
        return q_num in st.session_state.submitted_qs

    def start_exam(self, practice_set: str, exam_id: str, exam_data: Dict, mode: str):
        st.session_state.practice_set = practice_set
        st.session_state.exam_id = exam_id
        self.exam_data = exam_data
        self.mode = mode
        st.session_state.answers = {}
        st.session_state.submitted_qs = set()
        self.results = None
        self.focus_q = None
        if mode == "exam":
            self.end_time = time.time() + EXAM_DURATION_SECONDS
        else:
            self.end_time = None
        self.page = "exam"


class Navigation:
    def __init__(self, state: ExamState):
        self.state = state

    def go_welcome(self):
        self.state.reset()
        st.rerun()

    def go_mode_select(self):
        self.state.page = "mode_select"
        st.rerun()

    def go_exam(self, mode: str, practice_set: str, exam_id: str, exam_data: Dict):
        self.state.start_exam(practice_set, exam_id, exam_data, mode)
        st.rerun()

    def go_results(self, results: Dict):
        self.state.results = results
        self.state.page = "results"
        st.rerun()