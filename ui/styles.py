import streamlit as st


APP_CSS = """
    <style>
    .main { background-color: #f4f6fb; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] * { color: white !important; }

    [data-testid="stSidebar"] .stTextArea textarea {
        background: rgba(255,255,255,0.95) !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        border-radius: 8px !important;
        color: #1a202c !important;
        font-size: 0.88rem !important;
    }
    [data-testid="stSidebar"] .stTextArea textarea::placeholder {
        color: #718096 !important;
    }

    [data-testid="stSidebar"] .stFileUploader {
        background: rgba(255,255,255,0.95);
        border-radius: 10px;
        padding: 0.5rem;
    }
    [data-testid="stSidebar"] .stFileUploader label {
        color: white !important;
    }
    [data-testid="stSidebar"] .stFileUploader button {
        background: white !important;
        color: #667eea !important;
        border: 1px solid #667eea !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] .stFileUploader [data-testid="stFileUploaderDropzone"] {
        background: rgba(255,255,255,0.95) !important;
        border: 2px dashed rgba(102,126,234,0.5) !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] .stFileUploader [data-testid="stFileUploaderDropzone"] * {
        color: #4a5568 !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 0.65rem 1rem !important;
        width: 100% !important;
        margin-top: 0.5rem;
        transition: opacity 0.2s;
    }
    [data-testid="stSidebar"] .stButton > button:hover { opacity: 0.88 !important; }

    .title-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.2rem 2rem; border-radius: 16px;
        margin-bottom: 2rem; text-align: center;
        box-shadow: 0 4px 20px rgba(102,126,234,0.3);
    }
    .title-container h1 { color: white !important; font-size: 2.4rem; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
    .title-container p  { color: rgba(255,255,255,0.82); font-size: 1.05rem; margin-top: 0.4rem; }

    .empty-state {
        text-align: center; padding: 5rem 2rem;
        background: white; border-radius: 16px;
        border: 2px dashed #d0d7e8;
        margin-top: 1rem;
    }
    .empty-state .icon { font-size: 4rem; margin-bottom: 1rem; }
    .empty-state h2 { color: #2d3748; font-size: 1.6rem; font-weight: 700; margin: 0 0 0.5rem; }
    .empty-state p  { color: #718096; font-size: 1rem; margin: 0; }
    .empty-steps {
        display: flex; justify-content: center; gap: 2rem;
        margin-top: 2.5rem; flex-wrap: wrap;
    }
    .step-card {
        background: #f7f8fc; border-radius: 12px;
        padding: 1.2rem 1.5rem; min-width: 140px;
        text-align: center; border: 1px solid #e2e8f0;
    }
    .step-card .step-num {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white; border-radius: 50%; width: 32px; height: 32px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.9rem; margin: 0 auto 0.5rem;
    }
    .step-card p { font-size: 0.82rem; color: #4a5568; margin: 0; }

    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px; padding: 1.3rem;
        text-align: center; color: white;
        box-shadow: 0 3px 12px rgba(102,126,234,0.25);
    }
    .metric-card h3 { font-size: 2rem; font-weight: 800; margin: 0; }
    .metric-card p  { font-size: 0.82rem; opacity: 0.85; margin: 0.2rem 0 0; }

    .result-card {
        background: white; border-radius: 14px;
        padding: 1.3rem 1.5rem; margin-bottom: 1rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s;
    }
    .result-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
    .candidate-name { font-size: 1.1rem; font-weight: 700; color: #1a202c; margin-bottom: 0.15rem; }
    .skill-pill-matched {
        display: inline-block; background: #d4edda; color: #155724;
        border-radius: 20px; padding: 3px 10px;
        font-size: 0.76rem; font-weight: 500; margin: 2px;
    }
    .skill-pill-missing {
        display: inline-block; background: #f8d7da; color: #721c24;
        border-radius: 20px; padding: 3px 10px;
        font-size: 0.76rem; font-weight: 500; margin: 2px;
    }

    .section-header {
        font-size: 1.25rem; font-weight: 700;
        color: #1a202c; margin: 1.5rem 0 1rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e2e8f0;
    }

    .upload-count {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 8px; padding: 0.5rem 0.8rem;
        font-size: 0.85rem; margin-top: 0.4rem;
    }

    .stDownloadButton > button {
        background: white !important;
        color: #667eea !important;
        border: 2px solid #667eea !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s;
    }
    .stDownloadButton > button:hover {
        background: #667eea !important;
        color: white !important;
    }
    </style>
"""


def apply_app_styles() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def render_main_header() -> None:
    st.markdown(
        """
        <div class="title-container">
            <h1>📄 Resume Screener</h1>
            <p>Paste a job description, upload resumes, and get instant AI-powered candidate rankings</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scoring_expander() -> None:
    with st.expander("⚙️ How the score is calculated"):
        st.markdown(
            """
1. **Parse** — extract text from each PDF, split it into sections (Skills, Experience, Education, Projects, Certifications).
2. **Extract JD skills** — KeyBERT pulls the top keyphrases out of the job description.
3. **Embed** — the JD and each resume section are encoded into vectors with a Sentence-Transformer (`all-MiniLM-L6-v2`).
4. **Weighted score** — cosine similarity per section, combined using fixed weights: Skills 45% · Experience 35% · Projects 10% · Education 8% · Certifications 2%.
5. **Explain** — every resume keyword is compared to the JD individually to surface the top "boosters" and "draggers" behind the score.
            """
        )
