import streamlit as st
from api_client import APIClient
from state_nav import ExamState, Navigation
from ui_manager import UIManager

st.set_page_config(
    page_title="Security+ Practice",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Lora:wght@400;600&family=Space+Grotesk:wght@300;400;500;600&display=swap');

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

    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] { background-color: var(--bg-base) !important; color: var(--text-primary) !important; font-family: var(--font-body) !important; }
    [data-testid="stSidebar"] { background-color: var(--bg-surface) !important; border-right: 1px solid var(--border-subtle) !important; }
    [data-testid="stSidebar"] * { font-family: var(--font-ui) !important; }
    [data-testid="stMainBlockContainer"] { padding: 2rem 2.5rem !important; max-width: 900px !important; }

    h1 { font-family: var(--font-display) !important; font-size: 1.6rem !important; color: var(--amber) !important; letter-spacing: -0.02em; margin-bottom: 0.25rem !important; }
    h2 { font-family: var(--font-display) !important; font-size: 1.15rem !important; color: var(--text-primary) !important; }
    h3 { font-family: var(--font-ui) !important; font-weight: 500 !important; color: var(--text-secondary) !important; }
    p, li, label { font-family: var(--font-body) !important; line-height: 1.75 !important; }

    .q-card { background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 1.5rem 1.75rem; margin-bottom: 1.5rem; transition: border-color 0.2s; }
    .q-card:hover { border-color: var(--border-active); }
    .q-number { font-family: var(--font-display); font-size: 0.72rem; color: var(--amber); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.6rem; }
    .q-text { font-family: var(--font-body); font-size: 1.02rem; line-height: 1.8; color: var(--text-primary); margin-bottom: 1.2rem; }

    .feedback-correct { display: inline-block; background: var(--green-bg); color: var(--green); border: 1px solid var(--green); border-radius: var(--radius-sm); font-family: var(--font-ui); font-size: 0.78rem; padding: 0.2rem 0.65rem; margin-top: 0.6rem; font-weight: 500; }
    .feedback-wrong { display: inline-block; background: var(--red-bg); color: var(--red); border: 1px solid var(--red); border-radius: var(--radius-sm); font-family: var(--font-ui); font-size: 0.78rem; padding: 0.2rem 0.65rem; margin-top: 0.6rem; font-weight: 500; }
    .explanation-box { background: var(--bg-base); border-left: 3px solid var(--amber-dim); border-radius: 0 var(--radius-sm) var(--radius-sm) 0; padding: 0.85rem 1.1rem; margin-top: 0.9rem; font-family: var(--font-body); font-size: 0.93rem; color: var(--text-secondary); line-height: 1.75; }

    .timer-display { font-family: var(--font-display); font-size: 1.5rem; letter-spacing: 0.08em; text-align: center; padding: 0.6rem 0.8rem; border-radius: var(--radius-md); border: 1px solid var(--border-subtle); background: var(--bg-elevated); margin-bottom: 1rem; }
    .timer-ok    { color: var(--green); border-color: var(--green); }
    .timer-warn  { color: var(--amber); border-color: var(--amber); }
    .timer-crit  { color: var(--red); border-color: var(--red); animation: pulse 1s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }

    .set-card { background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 1.6rem 2rem; text-align: center; transition: border-color 0.2s, transform 0.15s; position: relative; overflow: hidden; }
    .set-card:hover { border-color: var(--amber-dim); transform: translateY(-2px); }
    .set-card.disabled { opacity: 0.45; cursor: not-allowed; }
    .set-card h2 { color: var(--text-primary) !important; margin-bottom: 0.5rem; }
    .set-card p  { color: var(--text-secondary); font-size: 0.9rem; }
    .wip-badge { position: absolute; top: 14px; right: 14px; background: var(--amber-dim); color: var(--amber); font-family: var(--font-display); font-size: 0.65rem; padding: 0.2rem 0.5rem; border-radius: 4px; letter-spacing: 0.08em; text-transform: uppercase; }

    .mode-card { background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 2rem; height: 100%; }
    .mode-card h3 { font-family: var(--font-display) !important; font-size: 1rem !important; color: var(--amber) !important; margin-bottom: 0.8rem !important; }
    .mode-card p { color: var(--text-secondary); font-size: 0.92rem; }

    .score-ring { text-align: center; padding: 2rem; background: var(--bg-surface); border-radius: var(--radius-lg); border: 1px solid var(--border-subtle); margin-bottom: 1.5rem; }
    .score-pct { font-family: var(--font-display); font-size: 3.5rem; color: var(--amber); letter-spacing: -0.03em; line-height: 1; }
    .score-sub { font-family: var(--font-ui); font-size: 0.9rem; color: var(--text-secondary); margin-top: 0.4rem; }
    .result-row { display: flex; align-items: flex-start; gap: 0.75rem; background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1rem 1.2rem; margin-bottom: 0.6rem; }
    .result-row.correct { border-left: 3px solid var(--green); }
    .result-row.wrong   { border-left: 3px solid var(--red); }
    .result-icon { font-size: 1rem; margin-top: 2px; flex-shrink: 0; }
    .result-body { flex: 1; }
    .result-qnum { font-family: var(--font-display); font-size: 0.7rem; color: var(--text-muted); letter-spacing: 0.08em; text-transform: uppercase; }
    .result-expl { font-size: 0.88rem; color: var(--text-secondary); margin-top: 0.4rem; line-height: 1.65; }

    hr { border: none; border-top: 1px solid var(--border-subtle) !important; margin: 1.5rem 0 !important; }
    .stCheckbox > label, .stRadio > label { color: var(--text-secondary) !important; font-family: var(--font-body) !important; }
    div[data-testid="stCheckbox"] { margin-bottom: 0.4rem; }

    .stButton > button { font-family: var(--font-ui) !important; font-size: 0.88rem !important; font-weight: 500 !important; border-radius: var(--radius-md) !important; border: 1px solid var(--border-active) !important; background: var(--bg-elevated) !important; color: var(--text-primary) !important; transition: all 0.15s !important; padding: 0.45rem 1rem !important; }
    .stButton > button:hover { border-color: var(--amber) !important; color: var(--amber) !important; background: rgba(240,168,48,0.06) !important; }
    .stButton > button[kind="primary"] { border-color: var(--amber) !important; background: rgba(240,168,48,0.10) !important; color: var(--amber) !important; }

    details summary { font-family: var(--font-ui) !important; font-size: 0.88rem !important; color: var(--text-secondary) !important; }
    details { background: var(--bg-elevated) !important; border-radius: var(--radius-sm) !important; border: 1px solid var(--border-subtle) !important; padding: 0.5rem 0.8rem !important; margin-top: 0.5rem; }

    #MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-base); }
    ::-webkit-scrollbar-thumb { background: var(--border-active); border-radius: 3px; }
    </style>
    """, unsafe_allow_html=True)

def main():
    inject_css()

    state = ExamState()
    api = APIClient()
    nav = Navigation(state)
    ui = UIManager(state, api, nav)

    ui.render_sidebar()

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