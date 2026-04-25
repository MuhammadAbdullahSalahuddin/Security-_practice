import streamlit as st
import time
from typing import Dict, List
from api_client import APIClient, parse_question_number
from state_nav import ExamState, Navigation

class UIManager:
    def __init__(self, state: ExamState, api: APIClient, nav: Navigation):
        self.state = state
        self.api = api
        self.nav = nav

    # ── Helpers ─────────────────────────────
    def _question_options(self, q: Dict) -> List[str]:
        return [opt["text"] for opt in q.get("all_options", [])]

    def _correct_indices(self, q: Dict) -> List[int]:
        return sorted(q.get("correct_indices", []))

    def _q_num(self, q: Dict):
        return parse_question_number(q.get("question_number", 0))

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

        st.markdown(f"<div class='timer-display {cls}'>{timer_str}</div>", unsafe_allow_html=True)

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
                "<div class='set-card'><h2>Practice Set 1</h2>"
                "<p>6 full-length practice exams covering all CompTIA Security+ SY0-701 domains.</p></div>",
                unsafe_allow_html=True,
            )
            if st.button("Open Practice Set 1 →", key="open_ps1", use_container_width=True, type="primary"):
                st.session_state._show_ps1 = True

        with col2:
            st.markdown(
                "<div class='set-card disabled'><span class='wip-badge'>Working on it</span>"
                "<h2>Practice Set 2</h2><p>Additional exam content coming soon.</p></div>",
                unsafe_allow_html=True,
            )
            st.button("Coming Soon", key="ps2_btn", disabled=True, use_container_width=True)

        if st.session_state.get("_show_ps1"):
            st.markdown("---")
            st.markdown("<h2>Practice Set 1 — Exams</h2>", unsafe_allow_html=True)

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

        st.markdown(f"<h1>Select Mode</h1><p style='color:var(--text-muted);font-family:var(--font-ui);font-size:0.88rem;margin-bottom:2rem;'>{exam_label}</p>", unsafe_allow_html=True)

        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown(
                "<div class='mode-card'><h3>📘 PRACTICE MODE</h3>"
                "<p>Instant feedback after each answer. Correct options highlighted. Explanations available immediately. No time limit.</p></div>",
                unsafe_allow_html=True,
            )
            if st.button("Start Practice Mode", key="start_practice", use_container_width=True, type="primary"):
                self.nav.go_exam("practice", **pending)

        with col2:
            st.markdown(
                "<div class='mode-card'><h3>⏱ EXAM MODE</h3>"
                "<p>Strict 2-hour countdown. No feedback during the exam. Change answers freely until you submit or time expires.</p></div>",
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

        if self.state.time_expired:
            st.warning("⏰ Time's up! Submitting your exam automatically...")
            self._submit_exam()
            return

        questions = exam.get("questions", [])
        mode = self.state.mode

        exam_label = exam.get("exam_id", "").replace("_", " ").title()
        mode_badge = "Practice Mode" if mode == "practice" else "Exam Mode"
        st.markdown(f"<h1>{exam_label}</h1><p style='font-family:var(--font-ui);font-size:0.82rem;color:var(--text-muted);margin-bottom:1.5rem;'>{mode_badge} · {len(questions)} questions</p>", unsafe_allow_html=True)

        focus = self.state.focus_q

        for q in questions:
            qn = self._q_num(q)
            anchor_id = f"q-anchor-{qn}"
            st.markdown(f"<div id='{anchor_id}'></div>", unsafe_allow_html=True)

            if focus == qn:
                st.markdown(f"<script>document.getElementById('{anchor_id}').scrollIntoView({{behavior:'smooth'}});</script>", unsafe_allow_html=True)
                self.state.focus_q = None

            self._render_question(q, qn, mode)

        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

        if mode == "exam":
            col1, col2 = st.columns()
            with col2:
                if st.button("Submit Exam", type="primary", use_container_width=True, key="submit_exam_btn"):
                    self._submit_exam()
        else:
            answered_count = len([v for v in self.state.answers.values() if v])
            st.caption(f"{answered_count}/{len(questions)} questions answered")
            if st.button("Finish & See Results", type="primary", use_container_width=True, key="finish_practice_btn"):
                self._submit_exam()

    def _render_question(self, q: Dict, qn, mode: str):
        options = self._question_options(q)
        correct = self._correct_indices(q)
        is_locked = self.state.is_locked(qn)
        current_sel = self.state.answers.get(qn, [])

        is_multi = len(correct) > 1 or q.get("question_type") == "multiple_choice"
        type_hint = f"Select {len(correct)}" if is_multi and len(correct) > 1 else "Select one"

        st.markdown(f"<div class='q-card'><div class='q-number'>Q {qn} &nbsp;·&nbsp; {type_hint}</div><div class='q-text'>{q.get('question_text','')}</div></div>", unsafe_allow_html=True)

        if is_multi:
            new_sel_texts = []
            for idx, opt_text in enumerate(options):
                label_text = opt_text
                if mode == "practice" and is_locked:
                    if idx in correct and idx in current_sel: label_text = f"✅ {opt_text}"
                    elif idx in correct: label_text = f"✅ {opt_text}"
                    elif idx in current_sel and idx not in correct: label_text = f"❌ {opt_text}"

                if st.checkbox(label_text, value=(idx in current_sel), key=f"opt_{qn}_{idx}", disabled=is_locked):
                    new_sel_texts.append(idx)

            if not is_locked:
                self.state.set_answer(qn, new_sel_texts)

        else:
            radio_options = options[:]
            if mode == "practice" and is_locked:
                decorated = []
                for idx, t in enumerate(options):
                    if idx in correct and idx in current_sel: decorated.append(f"✅ {t}")
                    elif idx in correct: decorated.append(f"✅ {t}")
                    elif idx in current_sel and idx not in correct: decorated.append(f"❌ {t}")
                    else: decorated.append(t)
                radio_options = decorated

            default_idx = current_sel if current_sel else None
            selected_label = st.radio(" ", radio_options, index=default_idx, key=f"radio_{qn}", disabled=is_locked, label_visibility="collapsed")

            if not is_locked and selected_label:
                sel_idx = radio_options.index(selected_label)
                self.state.set_answer(qn, [sel_idx])

        if mode == "practice":
            if not is_locked:
                if st.button("Check Answer", key=f"check_{qn}"):
                    self.state.lock_question(qn)
                    st.rerun()
            else:
                user_ans = sorted(self.state.answers.get(qn, []))
                if user_ans == correct: st.markdown("<span class='feedback-correct'>✓ Correct</span>", unsafe_allow_html=True)
                else: st.markdown("<span class='feedback-wrong'>✗ Incorrect</span>", unsafe_allow_html=True)

                expl = q.get("explanation", "")
                if expl:
                    with st.expander("📖 Explanation"):
                        st.markdown(f"<div class='explanation-box'>{expl}</div>", unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom:1.2rem'></div>", unsafe_allow_html=True)

    def _submit_exam(self):
        exam = self.state.exam_data
        with st.spinner("Grading..."):
            results = self.api.grade_exam(exam["practice_set"], exam["exam_id"], self.state.answers)
        if results:
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

        st.markdown("<h1>Results</h1>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"<div class='score-ring'><div class='score-pct' style='color:{color}'>{pct}%</div><div class='score-sub'>{badge}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='score-ring'><div class='score-pct'>{score}</div><div class='score-sub'>Correct</div></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='score-ring'><div class='score-pct'>{total - score}</div><div class='score-sub'>Incorrect</div></div>", unsafe_allow_html=True)

        st.markdown("<hr><h2 style='margin-bottom:1rem'>Question Breakdown</h2>", unsafe_allow_html=True)

        for detail in results.get("details", []):
            qn = detail.get("question_number")
            ok = detail.get("is_correct", False)
            q_text = detail.get("question_text", f"Question {qn}")
            expl = detail.get("explanation", "")
            correct_idxs = detail.get("correct_indices", [])
            all_opts = detail.get("all_options", [])

            row_cls = "correct" if ok else "wrong"
            icon = "✓" if ok else "✗"

            correct_texts = []
            if all_opts:
                for ci in correct_idxs:
                    if 0 <= ci < len(all_opts): correct_texts.append(all_opts[ci].get("text", ""))

            correct_str = "; ".join(correct_texts) if correct_texts else "—"

            st.markdown(
                f"<div class='result-row {row_cls}'>"
                f"  <div class='result-icon'>{icon}</div>"
                f"  <div class='result-body'>"
                f"    <div class='result-qnum'>Q {qn}</div>"
                f"    <div style='font-size:0.92rem;color:var(--text-primary);margin:0.25rem 0'>{q_text[:180]}{'…' if len(q_text)>180 else ''}</div>"
                f"    <div style='font-size:0.82rem;color:var(--text-muted)'>Correct: {correct_str}</div>"
                + (f"<div class='result-expl'>{expl}</div>" if expl else "")
                + f"  </div></div>",
                unsafe_allow_html=True,
            )

        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("⟵  Return to Home", type="primary"):
            self.nav.go_welcome()