"""
Security+ Practice Test — Streamlit Frontend
OOP architecture: APIClient, ExamState, UIManager, Navigation
"""

import streamlit as st
import requests
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
EXAM_DURATION_SECONDS = 7200

st.set_page_config(
    page_title="Security+ Practice",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS — "Terminal Slate" aesthetic
# Inspired by operator dashboards: deep navy canvas,
# warm amber accents, IBM Plex Mono for code feel,
# Lora for body text authority.
# ─────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Lora:wght@400;600&family=Space+Grotesk:wght@300;400;500;600&display=swap');

    /* ── Root variables ── */
    :root {
        --bg-base:        #0f1117;
        --bg-surface:     #171b26;
        --bg-elevated:    #1e2333;
        --bg-hover:       #252b3b;
        --border-subtle:  #2a3045;
        --border-active:  #3d4a6b;

        --text-primary:   #e8eaf0;
        --text-secondary: #8b93a8;
        --text-muted:     #525b72;

        --amber:          #f0a830;
        --amber-dim:      #8a5e18;
        --green:          #4caf87;
        --green-bg:       rgba(76,175,135,0.12);
        --red:            #e05c6a;
        --red-bg:         rgba(224,92,106,0.12);
        --blue:           #5b8ef0;
        --blue-bg:        rgba(91,142,240,0.10);

        --radius-sm:      6px;
        --radius-md:      10px;
        --radius-lg:      14px;

        --font-display:   'IBM Plex Mono', monospace;
        --font-body:      'Lora', Georgia, serif;
        --font-ui:        'Space Grotesk', sans-serif;
    }

    /* ── Global reset ── */
    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stApp"] {
        background-color: var(--bg-base) !important;
        color: var(--text-primary) !important;
        font-family: var(--font-body) !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--bg-surface) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    [data-testid="stSidebar"] * {
        font-family: var(--font-ui) !important;
    }

    /* Main content area */
    [data-testid="stMainBlockContainer"] {
        padding: 2rem 2.5rem !important;
        max-width: 900px !important;
    }

    /* ── Typography ── */
    h1 { font-family: var(--font-display) !important; font-size: 1.6rem !important;
         color: var(--amber) !important; letter-spacing: -0.02em; margin-bottom: 0.25rem !important; }
    h2 { font-family: var(--font-display) !important; font-size: 1.15rem !important;
         color: var(--text-primary) !important; }
    h3 { font-family: var(--font-ui) !important; font-weight: 500 !important;
         color: var(--text-secondary) !important; }

    p, li, label { font-family: var(--font-body) !important; line-height: 1.75 !important; }

    /* ── Question card ── */
    .q-card {
        background: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.5rem;
        transition: border-color 0.2s;
    }
    .q-card:hover { border-color: var(--border-active); }

    .q-number {
        font-family: var(--font-display);
        font-size: 0.72rem;
        color: var(--amber);
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.6rem;
    }
    .q-text {
        font-family: var(--font-body);
        font-size: 1.02rem;
        line-height: 1.8;
        color: var(--text-primary);
        margin-bottom: 1.2rem;
    }

    /* ── Option buttons ── */
    .opt-btn {
        display: block;
        width: 100%;
        text-align: left;
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 0.7rem 1rem;
        margin-bottom: 0.45rem;
        color: var(--text-primary);
        font-family: var(--font-body);
        font-size: 0.95rem;
        cursor: pointer;
        transition: background 0.15s, border-color 0.15s;
    }
    .opt-btn:hover { background: var(--bg-hover); border-color: var(--border-active); }
    .opt-btn.selected { border-color: var(--blue); background: var(--blue-bg); }
    .opt-btn.correct  { border-color: var(--green) !important; background: var(--green-bg) !important; color: var(--green) !important; }
    .opt-btn.wrong    { border-color: var(--red) !important; background: var(--red-bg) !important; color: var(--red) !important; }
    .opt-btn.locked   { cursor: default; opacity: 0.85; }

    /* ── Feedback badge ── */
    .feedback-correct {
        display: inline-block; background: var(--green-bg); color: var(--green);
        border: 1px solid var(--green); border-radius: var(--radius-sm);
        font-family: var(--font-ui); font-size: 0.78rem; padding: 0.2rem 0.65rem;
        margin-top: 0.6rem; font-weight: 500;
    }
    .feedback-wrong {
        display: inline-block; background: var(--red-bg); color: var(--red);
        border: 1px solid var(--red); border-radius: var(--radius-sm);
        font-family: var(--font-ui); font-size: 0.78rem; padding: 0.2rem 0.65rem;
        margin-top: 0.6rem; font-weight: 500;
    }

    /* ── Explanation box ── */
    .explanation-box {
        background: var(--bg-base);
        border-left: 3px solid var(--amber-dim);
        border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
        padding: 0.85rem 1.1rem;
        margin-top: 0.9rem;
        font-family: var(--font-body);
        font-size: 0.93rem;
        color: var(--text-secondary);
        line-height: 1.75;
    }

    /* ── Timer display ── */
    .timer-display {
        font-family: var(--font-display);
        font-size: 1.5rem;
        letter-spacing: 0.08em;
        text-align: center;
        padding: 0.6rem 0.8rem;
        border-radius: var(--radius-md);
        border: 1px solid var(--border-subtle);
        background: var(--bg-elevated);
        margin-bottom: 1rem;
    }
    .timer-ok    { color: var(--green); border-color: var(--green); }
    .timer-warn  { color: var(--amber); border-color: var(--amber); }
    .timer-crit  { color: var(--red); border-color: var(--red); animation: pulse 1s infinite; }

    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }

    /* ── Sidebar nav items ── */
    .sidebar-q-item {
        display: flex; align-items: center; gap: 0.5rem;
        padding: 0.35rem 0.6rem; border-radius: var(--radius-sm);
        font-family: var(--font-ui); font-size: 0.83rem;
        color: var(--text-secondary); cursor: pointer;
        transition: background 0.15s;
        margin-bottom: 2px;
    }
    .sidebar-q-item:hover { background: var(--bg-hover); color: var(--text-primary); }
    .sidebar-q-item.answered { color: var(--text-primary); }
    .sidebar-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
    .dot-unanswered { background: var(--text-muted); }
    .dot-correct    { background: var(--green); }
    .dot-wrong      { background: var(--red); }
    .dot-answered   { background: var(--blue); }

    /* ── Welcome cards ── */
    .set-card {
        background: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 1.6rem 2rem;
        text-align: center;
        transition: border-color 0.2s, transform 0.15s;
        position: relative;
        overflow: hidden;
    }
    .set-card:hover { border-color: var(--amber-dim); transform: translateY(-2px); }
    .set-card.disabled { opacity: 0.45; cursor: not-allowed; }
    .set-card h2 { color: var(--text-primary) !important; margin-bottom: 0.5rem; }
    .set-card p  { color: var(--text-secondary); font-size: 0.9rem; }

    .wip-badge {
        position: absolute; top: 14px; right: 14px;
        background: var(--amber-dim); color: var(--amber);
        font-family: var(--font-display); font-size: 0.65rem;
        padding: 0.2rem 0.5rem; border-radius: 4px;
        letter-spacing: 0.08em; text-transform: uppercase;
    }

    .exam-pill {
        display: inline-block;
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: 20px;
        padding: 0.4rem 1.1rem;
        font-family: var(--font-ui);
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin: 0.3rem;
        cursor: pointer;
        transition: all 0.15s;
    }
    .exam-pill:hover { border-color: var(--amber); color: var(--amber); }

    /* ── Mode cards ── */
    .mode-card {
        background: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 2rem;
        height: 100%;
    }
    .mode-card h3 { font-family: var(--font-display) !important;
                    font-size: 1rem !important; color: var(--amber) !important;
                    margin-bottom: 0.8rem !important; }
    .mode-card p { color: var(--text-secondary); font-size: 0.92rem; }

    /* ── Results ── */
    .score-ring {
        text-align: center;
        padding: 2rem;
        background: var(--bg-surface);
        border-radius: var(--radius-lg);
        border: 1px solid var(--border-subtle);
        margin-bottom: 1.5rem;
    }
    .score-pct {
        font-family: var(--font-display);
        font-size: 3.5rem;
        color: var(--amber);
        letter-spacing: -0.03em;
        line-height: 1;
    }
    .score-sub {
        font-family: var(--font-ui);
        font-size: 0.9rem;
        color: var(--text-secondary);
        margin-top: 0.4rem;
    }
    .result-row {
        display: flex; align-items: flex-start; gap: 0.75rem;
        background: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
    }
    .result-row.correct { border-left: 3px solid var(--green); }
    .result-row.wrong   { border-left: 3px solid var(--red); }
    .result-icon { font-size: 1rem; margin-top: 2px; flex-shrink: 0; }
    .result-body { flex: 1; }
    .result-qnum { font-family: var(--font-display); font-size: 0.7rem;
                   color: var(--text-muted); letter-spacing: 0.08em; text-transform: uppercase; }
    .result-expl { font-size: 0.88rem; color: var(--text-secondary);
                   margin-top: 0.4rem; line-height: 1.65; }

    /* ── Divider ── */
    hr { border: none; border-top: 1px solid var(--border-subtle) !important; margin: 1.5rem 0 !important; }

    /* ── Streamlit widget overrides ── */
    .stCheckbox > label, .stRadio > label {
        color: var(--text-secondary) !important;
        font-family: var(--font-body) !important;
    }
    div[data-testid="stCheckbox"] { margin-bottom: 0.4rem; }

    .stButton > button {
        font-family: var(--font-ui) !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--border-active) !important;
        background: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
        transition: all 0.15s !important;
        padding: 0.45rem 1rem !important;
    }
    .stButton > button:hover {
        border-color: var(--amber) !important;
        color: var(--amber) !important;
        background: rgba(240,168,48,0.06) !important;
    }
    .stButton > button[kind="primary"] {
        border-color: var(--amber) !important;
        background: rgba(240,168,48,0.10) !important;
        color: var(--amber) !important;
    }

    /* expander */
    details summary {
        font-family: var(--font-ui) !important;
        font-size: 0.88rem !important;
        color: var(--text-secondary) !important;
    }
    details { background: var(--bg-elevated) !important;
              border-radius: var(--radius-sm) !important;
              border: 1px solid var(--border-subtle) !important;
              padding: 0.5rem 0.8rem !important;
              margin-top: 0.5rem; }

    /* remove Streamlit branding */
    #MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

    /* scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-base); }
    ::-webkit-scrollbar-thumb { background: var(--border-active); border-radius: 3px; }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
import re as _re

def _parse_question_number(raw) -> int:
    """Convert any question_number representation to int.
    Handles: 1, "1", "Question 1", "Question 1:", etc.
    The scraper stores question_number as "Question N" strings in MongoDB.
    """
    if isinstance(raw, int):
        return raw
    m = _re.search(r'\d+', str(raw))
    return int(m.group()) if m else 0


# ─────────────────────────────────────────────
# API CLIENT
# ─────────────────────────────────────────────
class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url

    def get_exams(self) -> List[Dict]:
        try:
            r = requests.get(f"{self.base_url}/exams", timeout=5)
            return r.json().get("data", [])
        except requests.exceptions.ConnectionError:
            st.error("⚠  Cannot reach API. Make sure the FastAPI backend is running on port 8000.")
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
            # q_num is the raw question_number from MongoDB ("Question 1", etc.)
            # _parse_question_number strips that to a plain int for Pydantic
            user_answers.append({
                "question_number": _parse_question_number(q_num),
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


# ─────────────────────────────────────────────
# EXAM STATE
# ─────────────────────────────────────────────
class ExamState:
    """Wraps st.session_state with typed accessors."""

    DEFAULTS: Dict[str, Any] = {
        "page": "welcome",          # welcome | mode_select | exam | results
        "mode": None,               # practice | exam
        "practice_set": None,
        "exam_id": None,
        "exam_data": None,
        "answers": {},              # {q_num: [selected_indices]}
        "submitted_qs": set(),      # practice: locked questions
        "results": None,
        "end_time": None,
        "focus_q": None,            # sidebar jump target
    }

    def __init__(self):
        for k, v in self.DEFAULTS.items():
            if k not in st.session_state:
                st.session_state[k] = v

    def reset(self):
        for k, v in self.DEFAULTS.items():
            st.session_state[k] = v

    # ── Convenience properties ──
    @property
    def page(self) -> str:
        return st.session_state.page

    @page.setter
    def page(self, v: str):
        st.session_state.page = v

    @property
    def mode(self) -> Optional[str]:
        return st.session_state.mode

    @mode.setter
    def mode(self, v: str):
        st.session_state.mode = v

    @property
    def exam_data(self) -> Optional[Dict]:
        return st.session_state.exam_data

    @exam_data.setter
    def exam_data(self, v):
        st.session_state.exam_data = v

    @property
    def answers(self) -> Dict:
        return st.session_state.answers

    @property
    def submitted_qs(self) -> set:
        return st.session_state.submitted_qs

    @property
    def results(self):
        return st.session_state.results

    @results.setter
    def results(self, v):
        st.session_state.results = v

    @property
    def end_time(self) -> Optional[float]:
        return st.session_state.end_time

    @end_time.setter
    def end_time(self, v):
        st.session_state.end_time = v

    @property
    def focus_q(self):
        return st.session_state.focus_q

    @focus_q.setter
    def focus_q(self, v):
        st.session_state.focus_q = v

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


# ─────────────────────────────────────────────
# NAVIGATION
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# UI MANAGER
# ─────────────────────────────────────────────
class UIManager:
    def __init__(self, state: ExamState, api: APIClient, nav: Navigation):
        self.state = state
        self.api = api
        self.nav = nav

    # ── Helpers ─────────────────────────────
    def _question_options(self, q: Dict) -> List[str]:
        """Return display texts for a question's options."""
        return [opt["text"] for opt in q.get("all_options", [])]

    def _correct_indices(self, q: Dict) -> List[int]:
        return sorted(q.get("correct_indices", []))

    def _q_num(self, q: Dict):
        """Normalise question_number to int.
        Handles both plain integers and 'Question N' strings from MongoDB."""
        raw = q.get("question_number", 0)
        return _parse_question_number(raw)

    # ── Sidebar ─────────────────────────────
    def render_sidebar(self):
        if self.state.page not in ("exam",):
            return

        exam = self.state.exam_data
        if not exam:
            return

        questions = exam.get("questions", [])
        mode = self.state.mode

        with st.sidebar:
            st.markdown(
                f"<div style='font-family:var(--font-display);font-size:0.75rem;"
                f"color:var(--amber);letter-spacing:0.12em;text-transform:uppercase;"
                f"margin-bottom:1rem'>"
                f"{'PRACTICE' if mode == 'practice' else 'EXAM'} · "
                f"{exam.get('exam_id','').replace('_',' ').upper()}</div>",
                unsafe_allow_html=True,
            )

            if mode == "exam" and self.state.end_time:
                self._render_timer()

            st.markdown("---")
            st.markdown(
                "<div style='font-family:var(--font-ui);font-size:0.72rem;"
                "color:var(--text-muted);margin-bottom:0.6rem;'>QUESTIONS</div>",
                unsafe_allow_html=True,
            )

            answered = self.state.answers
            submitted = self.state.submitted_qs

            for q in questions:
                qn = self._q_num(q)
                has_answer = bool(answered.get(qn))

                if mode == "practice" and qn in submitted:
                    user_ans = sorted(answered.get(qn, []))
                    correct = self._correct_indices(q)
                    if user_ans == correct:
                        dot_cls, icon = "dot-correct", "✓"
                    else:
                        dot_cls, icon = "dot-wrong", "✗"
                elif has_answer:
                    dot_cls, icon = "dot-answered", "·"
                else:
                    dot_cls, icon = "dot-unanswered", "·"

                # Jump link via anchor
                jump_key = f"jump_{qn}"
                if st.button(f"Q{qn}  {icon}", key=jump_key, use_container_width=True):
                    self.state.focus_q = qn
                    st.rerun()

            st.markdown("---")
            if st.button("⟵  Exit Exam", use_container_width=True):
                self.nav.go_welcome()

    def _render_timer(self):
        remaining = max(0, int(self.state.end_time - time.time()))
        hours, rem = divmod(remaining, 3600)
        mins, secs = divmod(rem, 60)
        timer_str = f"{hours:02d}:{mins:02d}:{secs:02d}"

        if remaining > 1800:
            cls = "timer-ok"
        elif remaining > 300:
            cls = "timer-warn"
        else:
            cls = "timer-crit"

        st.markdown(
            f"<div class='timer-display {cls}'>{timer_str}</div>",
            unsafe_allow_html=True,
        )

    # ── Welcome ─────────────────────────────
    def render_welcome(self):
        st.markdown(
            "<h1>🛡 Security+ · Practice Engine</h1>"
            "<p style='color:var(--text-muted);font-family:var(--font-ui);font-size:0.88rem;"
            "margin-bottom:2rem;'>Select a practice set to begin.</p>",
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown(
                "<div class='set-card'>"
                "<h2>Practice Set 1</h2>"
                "<p>6 full-length practice exams covering all CompTIA Security+ SY0-701 domains.</p>"
                "</div>",
                unsafe_allow_html=True,
            )
            if st.button("Open Practice Set 1 →", key="open_ps1", use_container_width=True, type="primary"):
                st.session_state._show_ps1 = True

        with col2:
            st.markdown(
                "<div class='set-card disabled'>"
                "<span class='wip-badge'>Working on it</span>"
                "<h2>Practice Set 2</h2>"
                "<p>Additional exam content coming soon.</p>"
                "</div>",
                unsafe_allow_html=True,
            )
            st.button("Coming Soon", key="ps2_btn", disabled=True, use_container_width=True)

        # Exam list for Practice Set 1
        if st.session_state.get("_show_ps1"):
            st.markdown("---")
            st.markdown(
                "<h2>Practice Set 1 — Exams</h2>",
                unsafe_allow_html=True,
            )

            all_sets = self.api.get_exams()
            ps1 = next((s for s in all_sets if "1" in s.get("_id", "")), None)

            if ps1:
                exams_sorted = sorted(ps1.get("exams", []))
                cols = st.columns(min(len(exams_sorted), 6))
                for i, eid in enumerate(exams_sorted):
                    with cols[i]:
                        label = eid.replace("_", " ").title()
                        if st.button(label, key=f"exam_{eid}", use_container_width=True):
                            exam_data = self.api.get_exam(ps1["_id"], eid)
                            if exam_data:
                                st.session_state._pending_exam = {
                                    "practice_set": ps1["_id"],
                                    "exam_id": eid,
                                    "exam_data": exam_data,
                                }
                                st.session_state.page = "mode_select"
                                st.rerun()
            else:
                st.warning("No exams found. Make sure the database is seeded.")

    # ── Mode Selection ───────────────────────
    def render_mode_select(self):
        pending = st.session_state.get("_pending_exam", {})
        exam_label = pending.get("exam_id", "").replace("_", " ").title()

        st.markdown(
            f"<h1>Select Mode</h1>"
            f"<p style='color:var(--text-muted);font-family:var(--font-ui);font-size:0.88rem;"
            f"margin-bottom:2rem;'>{exam_label}</p>",
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown(
                "<div class='mode-card'>"
                "<h3>📘 PRACTICE MODE</h3>"
                "<p>Instant feedback after each answer. Correct options highlighted. "
                "Explanations available immediately. No time limit.</p>"
                "</div>",
                unsafe_allow_html=True,
            )
            if st.button("Start Practice Mode", key="start_practice", use_container_width=True, type="primary"):
                self.nav.go_exam("practice", **pending)

        with col2:
            st.markdown(
                "<div class='mode-card'>"
                "<h3>⏱ EXAM MODE</h3>"
                "<p>Strict 2-hour countdown. No feedback during the exam. "
                "Change answers freely until you submit or time expires.</p>"
                "</div>",
                unsafe_allow_html=True,
            )
            if st.button("Start Exam Mode", key="start_exam", use_container_width=True):
                self.nav.go_exam("exam", **pending)

        st.markdown("---")
        if st.button("⟵  Back", key="mode_back"):
            self.state.page = "welcome"
            st.rerun()

    # ── Exam Page ────────────────────────────
    def render_exam(self):
        exam = self.state.exam_data
        if not exam:
            st.error("No exam loaded.")
            self.nav.go_welcome()
            return

        # Check timer expiry
        if self.state.time_expired:
            st.warning("⏰ Time's up! Submitting your exam automatically...")
            self._submit_exam()
            return

        questions = exam.get("questions", [])
        mode = self.state.mode

        # Header
        exam_label = exam.get("exam_id", "").replace("_", " ").title()
        mode_badge = "Practice Mode" if mode == "practice" else "Exam Mode"
        st.markdown(
            f"<h1>{exam_label}</h1>"
            f"<p style='font-family:var(--font-ui);font-size:0.82rem;color:var(--text-muted);"
            f"margin-bottom:1.5rem;'>{mode_badge} · {len(questions)} questions</p>",
            unsafe_allow_html=True,
        )

        # Jump anchor handling
        focus = self.state.focus_q

        for q in questions:
            qn = self._q_num(q)
            anchor_id = f"q-anchor-{qn}"

            # Scroll-to anchor (HTML trick)
            st.markdown(f"<div id='{anchor_id}'></div>", unsafe_allow_html=True)

            # Auto-scroll JS if this is the focus target
            if focus == qn:
                st.markdown(
                    f"<script>document.getElementById('{anchor_id}').scrollIntoView({{behavior:'smooth'}});</script>",
                    unsafe_allow_html=True,
                )
                self.state.focus_q = None

            self._render_question(q, qn, mode)

        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

        if mode == "exam":
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Submit Exam", type="primary", use_container_width=True, key="submit_exam_btn"):
                    self._submit_exam()
        else:
            answered_count = len([v for v in self.state.answers.values() if v])
            total = len(questions)
            st.caption(f"{answered_count}/{total} questions answered")
            if st.button("Finish & See Results", type="primary", use_container_width=True, key="finish_practice_btn"):
                self._submit_exam()

    def _render_question(self, q: Dict, qn, mode: str):
        options = self._question_options(q)
        correct = self._correct_indices(q)
        is_locked = self.state.is_locked(qn)
        current_sel = self.state.answers.get(qn, [])

        is_multi = len(correct) > 1 or q.get("question_type") == "multiple_choice"
        type_hint = f"Select {len(correct)}" if is_multi and len(correct) > 1 else "Select one"

        # Card header
        st.markdown(
            f"<div class='q-card'>"
            f"<div class='q-number'>Q {qn} &nbsp;·&nbsp; {type_hint}</div>"
            f"<div class='q-text'>{q.get('question_text','')}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Options — rendered as checkboxes/radio below the card
        if is_multi:
            new_sel_texts = []
            for idx, opt_text in enumerate(options):
                checked_default = idx in current_sel
                disabled_kwarg = is_locked

                label_text = opt_text
                if mode == "practice" and is_locked:
                    if idx in correct and idx in current_sel:
                        label_text = f"✅ {opt_text}"
                    elif idx in correct:
                        label_text = f"✅ {opt_text}"
                    elif idx in current_sel and idx not in correct:
                        label_text = f"❌ {opt_text}"

                checked = st.checkbox(
                    label_text,
                    value=checked_default,
                    key=f"opt_{qn}_{idx}",
                    disabled=disabled_kwarg,
                )
                if checked:
                    new_sel_texts.append(idx)

            if not is_locked:
                self.state.set_answer(qn, new_sel_texts)

        else:
            # Single choice — radio
            radio_options = options[:]
            if mode == "practice" and is_locked:
                decorated = []
                for idx, t in enumerate(options):
                    if idx in correct and idx in current_sel:
                        decorated.append(f"✅ {t}")
                    elif idx in correct:
                        decorated.append(f"✅ {t}")
                    elif idx in current_sel and idx not in correct:
                        decorated.append(f"❌ {t}")
                    else:
                        decorated.append(t)
                radio_options = decorated

            default_idx = current_sel[0] if current_sel else None

            selected_label = st.radio(
                " ",
                radio_options,
                index=default_idx,
                key=f"radio_{qn}",
                disabled=is_locked,
                label_visibility="collapsed",
            )

            if not is_locked and selected_label:
                # Map back to index in original options
                sel_idx = radio_options.index(selected_label)
                self.state.set_answer(qn, [sel_idx])

        # Practice mode submit + feedback
        if mode == "practice":
            if not is_locked:
                if st.button("Check Answer", key=f"check_{qn}"):
                    self.state.lock_question(qn)
                    st.rerun()
            else:
                user_ans = sorted(self.state.answers.get(qn, []))
                if user_ans == correct:
                    st.markdown("<span class='feedback-correct'>✓ Correct</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='feedback-wrong'>✗ Incorrect</span>", unsafe_allow_html=True)

                expl = q.get("explanation", "")
                if expl:
                    with st.expander("📖 Explanation"):
                        st.markdown(
                            f"<div class='explanation-box'>{expl}</div>",
                            unsafe_allow_html=True,
                        )

        st.markdown("<div style='margin-bottom:1.2rem'></div>", unsafe_allow_html=True)

    def _submit_exam(self):
        exam = self.state.exam_data
        with st.spinner("Grading..."):
            results = self.api.grade_exam(
                exam["practice_set"],
                exam["exam_id"],
                self.state.answers,
            )
        if results:
            # Attach question text for results page
            q_lookup = {self._q_num(q): q for q in exam.get("questions", [])}
            for detail in results.get("details", []):
                qn = detail.get("question_number")
                q = q_lookup.get(qn, {})
                detail["question_text"] = q.get("question_text", "")
                detail["all_options"] = q.get("all_options", [])
            self.nav.go_results(results)

    # ── Results Page ─────────────────────────
    def render_results(self):
        results = self.state.results
        if not results:
            self.nav.go_welcome()
            return

        pct = results.get("percentage", 0)
        score = results.get("score", 0)
        total = results.get("total_questions", 0)
        passing = pct >= 75

        color = "var(--green)" if passing else "var(--red)"
        badge = "PASS" if passing else "FAIL"

        st.markdown(
            f"<h1>Results</h1>",
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"<div class='score-ring'>"
                f"<div class='score-pct' style='color:{color}'>{pct}%</div>"
                f"<div class='score-sub'>{badge}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"<div class='score-ring'>"
                f"<div class='score-pct'>{score}</div>"
                f"<div class='score-sub'>Correct</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"<div class='score-ring'>"
                f"<div class='score-pct'>{total - score}</div>"
                f"<div class='score-sub'>Incorrect</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            "<h2 style='margin-bottom:1rem'>Question Breakdown</h2>",
            unsafe_allow_html=True,
        )

        for detail in results.get("details", []):
            qn = detail.get("question_number")
            ok = detail.get("is_correct", False)
            q_text = detail.get("question_text", f"Question {qn}")
            expl = detail.get("explanation", "")
            correct_idxs = detail.get("correct_indices", [])
            all_opts = detail.get("all_options", [])

            row_cls = "correct" if ok else "wrong"
            icon = "✓" if ok else "✗"

            # Correct answer text
            correct_texts = []
            if all_opts:
                for ci in correct_idxs:
                    if 0 <= ci < len(all_opts):
                        correct_texts.append(all_opts[ci].get("text", ""))

            correct_str = "; ".join(correct_texts) if correct_texts else "—"

            st.markdown(
                f"<div class='result-row {row_cls}'>"
                f"  <div class='result-icon'>{icon}</div>"
                f"  <div class='result-body'>"
                f"    <div class='result-qnum'>Q {qn}</div>"
                f"    <div style='font-size:0.92rem;color:var(--text-primary);margin:0.25rem 0'>{q_text[:180]}{'…' if len(q_text)>180 else ''}</div>"
                f"    <div style='font-size:0.82rem;color:var(--text-muted)'>Correct: {correct_str}</div>"
                + (f"<div class='result-expl'>{expl}</div>" if expl else "")
                + f"  </div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("⟵  Return to Home", type="primary", use_container_width=False):
            self.nav.go_welcome()


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────
def main():
    inject_css()

    state = ExamState()
    api = APIClient()
    nav = Navigation(state)
    ui = UIManager(state, api, nav)

    # Render sidebar (only visible during exam)
    ui.render_sidebar()

    # Route to current page
    page = state.page
    if page == "welcome":
        ui.render_welcome()
    elif page == "mode_select":
        ui.render_mode_select()
    elif page == "exam":
        ui.render_exam()
    elif page == "results":
        ui.render_results()
    else:
        state.page = "welcome"
        st.rerun()


if __name__ == "__main__":
    main()