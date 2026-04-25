import streamlit as st
import requests
import time

# When containerized, this will become http://api:8000/api/v1
API_BASE_URL = "http://127.0.0.1:8000/api/v1"

st.set_page_config(page_title="Security+ Practice", page_icon="🛡️", layout="wide")

# --- Session State Initialization ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "welcome"
if "exam_data" not in st.session_state:
    st.session_state.exam_data = None
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "mode" not in st.session_state:
    st.session_state.mode = None

# --- Helper Functions ---
def fetch_exams():
    try:
        response = requests.get(f"{API_BASE_URL}/exams")
        return response.json().get("data", [])
    except requests.exceptions.ConnectionError:
        st.error("API is offline. Please ensure the FastAPI backend is running.")
        return []

# --- Pages ---
def welcome_screen():
    st.title("🛡️ Welcome to Security+ Practice Test")
    st.write("Select a practice set and an exam to begin.")
    
    available_sets = fetch_exams()
    if not available_sets:
        return
        
    for practice_set in available_sets:
        st.subheader(practice_set["_id"].replace("_", " ").title())
        cols = st.columns(len(practice_set["exams"]))
        for i, exam_id in enumerate(practice_set["exams"]):
            with cols[i]:
                if st.button(f"{exam_id.replace('_', ' ').title()}", key=f"btn_{practice_set['_id']}_{exam_id}", use_container_width=True):
                    resp = requests.get(f"{API_BASE_URL}/exams/{practice_set['_id']}/{exam_id}")
                    if resp.status_code == 200:
                        st.session_state.exam_data = resp.json()
                        st.session_state.current_page = "mode_select"
                        st.session_state.answers.clear() # Clear old answers
                        st.rerun()

def mode_selection():
    st.title("Select Your Mode")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("### 📘 Practice Mode\nTake your time. Get instant feedback and explanations as you answer.")
        if st.button("Start Practice Mode", use_container_width=True):
            st.session_state.mode = "practice"
            st.session_state.current_page = "exam"
            st.rerun()
            
    with col2:
        st.warning("### ⏳ Exam Mode\nStrict 2-hour timer. Simulates the real testing environment. No instant feedback.")
        if st.button("Start Exam Mode", use_container_width=True):
            st.session_state.mode = "exam"
            st.session_state.end_time = time.time() + 7200 # 2 hours
            st.session_state.current_page = "exam"
            st.rerun()

def render_exam():
    exam = st.session_state.exam_data
    st.title(f"{exam['course']} - {exam['exam_id'].replace('_', ' ').title()}")
    
    # Timer Logic for Exam Mode
    if st.session_state.mode == "exam":
        time_left = max(0, int(st.session_state.end_time - time.time()))
        mins, secs = divmod(time_left, 60)
        st.sidebar.metric("⏳ Time Remaining", f"{mins:02d}:{secs:02d}")
        if time_left == 0:
            st.error("Time is up! Please submit your exam.")
    
    st.write("---")
    
    for q in exam['questions']:
        st.markdown(f"**Question {q['question_number']}**")
        st.write(q['question_text'])
        
        if q.get("screenshot_path"):
            st.caption(f"*(Exhibit tied to: {q['screenshot_path']})*")
            
        options = [opt['text'] for opt in q['all_options']]
        
        selected = st.multiselect(
            "Select your answer(s):", 
            options, 
            key=f"q_{q['question_number']}"
        )
        
        selected_indices = [q['all_options'][options.index(s)]['index'] for s in selected]
        st.session_state.answers[q['question_number']] = selected_indices
        
        # --- TRUE PRACTICE MODE LOGIC ---
        if st.session_state.mode == "practice" and selected_indices:
            actual_correct = q.get("correct_indices", [])
            is_correct = sorted(selected_indices) == sorted(actual_correct)
            
            if is_correct:
                st.success("✅ Correct!")
            else:
                st.error("❌ Incorrect")
                
            # Dropdown for explanation
            with st.expander("📖 View Explanation", expanded=not is_correct):
                st.info(q.get("explanation", "No explanation provided for this question."))
                st.write(f"**Correct Answer Indices:** {actual_correct}")

        st.write("---")
        
    if st.button("Submit Exam", type="primary", use_container_width=True):
        submit_exam()

def submit_exam():
    exam = st.session_state.exam_data
    
    # Force cast question_number to int to satisfy Pydantic
    clean_answers = []
    for k, v in st.session_state.answers.items():
        try:
            q_num = int(k)
        except ValueError:
            q_num = k # Fallback if it's deeply weird data
        clean_answers.append({"question_number": q_num, "selected_indices": v})

    payload = {
        "practice_set": exam["practice_set"],
        "exam_id": exam["exam_id"],
        "user_answers": clean_answers
    }
    
    with st.spinner("Grading..."):
        try:
            response = requests.post(f"{API_BASE_URL}/grade", json=payload)
            if response.status_code == 200:
                st.session_state.results = response.json()
                st.session_state.current_page = "results"
                st.rerun()
            else:
                # If it fails, print the exact JSON error to the screen so we can debug it
                st.error(f"❌ Backend Rejected Submission (Status {response.status_code})")
                st.json(response.json())
        except Exception as e:
            st.error(f"Connection Error: {e}")

def render_results():
    results = st.session_state.results
    st.title("📊 Exam Results")
    
    st.metric("Final Score", f"{results['score']} / {results['total_questions']}", f"{results['percentage']}%")
    st.write("---")
    
    st.subheader("Question Breakdown")
    for detail in results["details"]:
        status = "✅ Correct" if detail["is_correct"] else "❌ Incorrect"
        
        with st.expander(f"Question {detail['question_number']}: {status}"):
            st.write(f"**Explanation:** {detail.get('explanation', 'No explanation provided.')}")
            
    st.write("---")
    if st.button("Return to Home"):
        st.session_state.clear()
        st.rerun()

# --- Page Router ---
if st.session_state.current_page == "welcome":
    welcome_screen()
elif st.session_state.current_page == "mode_select":
    mode_selection()
elif st.session_state.current_page == "exam":
    render_exam()
elif st.session_state.current_page == "results":
    render_results()