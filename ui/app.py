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
        # Create a dynamic row of buttons for the exams
        cols = st.columns(len(practice_set["exams"]))
        for i, exam_id in enumerate(practice_set["exams"]):
            with cols[i]:
                if st.button(f"{exam_id.replace('_', ' ').title()}", key=f"btn_{practice_set['_id']}_{exam_id}", use_container_width=True):
                    resp = requests.get(f"{API_BASE_URL}/exams/{practice_set['_id']}/{exam_id}")
                    if resp.status_code == 200:
                        st.session_state.exam_data = resp.json()
                        st.session_state.current_page = "mode_select"
                        st.rerun()

def mode_selection():
    st.title("Select Your Mode")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("### 📘 Practice Mode\nTake your time. See correct answers and explanations at the end.")
        if st.button("Start Practice Mode", use_container_width=True):
            st.session_state.mode = "practice"
            st.session_state.current_page = "exam"
            st.rerun()
            
    with col2:
        st.warning("### ⏳ Exam Mode\nStrict 2-hour timer. Simulates the real testing environment.")
        if st.button("Start Exam Mode", use_container_width=True):
            st.session_state.mode = "exam"
            st.session_state.end_time = time.time() + 7200 # 2 hours in seconds
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
    
    # Render all questions
    for q in exam['questions']:
        st.markdown(f"**Question {q['question_number']}**")
        st.write(q['question_text'])
        
        # Display image placeholder if a screenshot path exists
        if q.get("screenshot_path"):
            st.caption(f"*(Exhibit tied to: {q['screenshot_path']})*")
            
        options = [opt['text'] for opt in q['all_options']]
        
        # Determine if we need checkboxes (multiple choice) or radio buttons (single choice)
        # For this MVP, we use multiselect to safely handle questions with 1 or more answers
        selected = st.multiselect(
            "Select your answer(s):", 
            options, 
            key=f"q_{q['question_number']}"
        )
        
        # Save the indices of the selected options
        selected_indices = [q['all_options'][options.index(s)]['index'] for s in selected]
        st.session_state.answers[q['question_number']] = selected_indices
        st.write("---")
        
    if st.button("Submit Exam", type="primary", use_container_width=True):
        submit_exam()

def submit_exam():
    exam = st.session_state.exam_data
    payload = {
        "practice_set": exam["practice_set"],
        "exam_id": exam["exam_id"],
        "user_answers": [
            {"question_number": k, "selected_indices": v} 
            for k, v in st.session_state.answers.items()
        ]
    }
    
    # Send to FastAPI for grading
    with st.spinner("Grading..."):
        response = requests.post(f"{API_BASE_URL}/grade", json=payload)
        if response.status_code == 200:
            st.session_state.results = response.json()
            st.session_state.current_page = "results"
            st.rerun()
        else:
            st.error("An error occurred while grading.")

def render_results():
    results = st.session_state.results
    st.title("📊 Exam Results")
    
    # Score display
    st.metric("Final Score", f"{results['score']} / {results['total_questions']}", f"{results['percentage']}%")
    st.write("---")
    
    # Detailed breakdown
    st.subheader("Question Breakdown")
    for detail in results["details"]:
        color = "green" if detail["is_correct"] else "red"
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