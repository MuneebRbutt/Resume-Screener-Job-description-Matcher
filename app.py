import streamlit as st
import pandas as pd
from resume_parser import extract_text_from_pdf
from nlp_engine import rank_resumes

# Page config
st.set_page_config(
    page_title="Resume Screener",
    page_icon="📄",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .title-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .title-container h1 {
        color: white !important;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    .title-container p {
        color: rgba(255,255,255,0.85);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    .section-card {
        background: white;
        border-radius: 12px;
        padding: 1.8rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        border: 1px solid #e9ecef;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #495057;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        color: white;
    }
    .metric-card h3 {
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    .metric-card p {
        font-size: 0.85rem;
        opacity: 0.85;
        margin: 0;
    }
    .rank-1 { background: linear-gradient(135deg, #f6d365 0%, #fda085 100%); }
    .rank-2 { background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: #333 !important; }
    .rank-3 { background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%); color: #333 !important; }
    .result-row {
        display: flex;
        align-items: center;
        padding: 1rem 1.2rem;
        border-radius: 10px;
        margin-bottom: 0.8rem;
        background: white;
        border: 1px solid #e9ecef;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        width: 100%;
        transition: opacity 0.2s;
    }
    .stButton > button:hover {
        opacity: 0.9;
        color: white;
    }
    .stTextArea textarea {
        border-radius: 8px;
        border: 1px solid #dee2e6;
        font-size: 0.95rem;
    }
    .upload-count {
        background: #e8f4fd;
        border: 1px solid #bee3f8;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        color: #2b6cb0;
        font-size: 0.9rem;
        font-weight: 500;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="title-container">
        <h1>📄 Resume Screener</h1>
        <p>Upload a job description and resumes to instantly find the best candidates</p>
    </div>
""", unsafe_allow_html=True)

# Layout: two columns
col1, col2 = st.columns([1.2, 1], gap="large")

with col1:
    st.markdown('<div class="section-title">📋 Job Description</div>', unsafe_allow_html=True)
    job_description = st.text_area(
        label="",
        height=280,
        placeholder="Paste the job description here...\n\nExample: We are looking for a Python developer with experience in NLP, machine learning, and REST APIs...",
        label_visibility="collapsed"
    )

with col2:
    st.markdown('<div class="section-title">📁 Upload Resumes</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        label="",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    if uploaded_files:
        st.markdown(f'<div class="upload-count">✅ {len(uploaded_files)} resume(s) uploaded and ready</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="upload-count">📂 No resumes uploaded yet — supports PDF only</div>', unsafe_allow_html=True)

# Screen button
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    screen_btn = st.button("🔍 Screen Resumes")

# Processing
if screen_btn:
    if not job_description.strip():
        st.warning("⚠️ Please enter a job description before screening.")
    elif not uploaded_files:
        st.warning("⚠️ Please upload at least one resume.")
    else:
        with st.spinner("🤖 Analyzing resumes with NLP..."):
            resumes = {}
            failed = []
            for file in uploaded_files:
                text = extract_text_from_pdf(file)
                if text:
                    resumes[file.name] = text
                else:
                    failed.append(file.name)

            if failed:
                st.error(f"Could not extract text from: {', '.join(failed)}")

            if resumes:
                results = rank_resumes(job_description, resumes)

                st.markdown("---")
                st.markdown("## 🏆 Results")

                # Summary metrics
                m1, m2, m3 = st.columns(3)
                top_score = results[0][1] * 100 if results else 0
                avg_score = sum(r[1] for r in results) / len(results) * 100 if results else 0

                with m1:
                    st.markdown(f"""
                        <div class="metric-card rank-1">
                            <h3>{len(results)}</h3>
                            <p>Resumes Screened</p>
                        </div>
                    """, unsafe_allow_html=True)
                with m2:
                    st.markdown(f"""
                        <div class="metric-card rank-1">
                            <h3>{top_score:.1f}%</h3>
                            <p>Top Match Score</p>
                        </div>
                    """, unsafe_allow_html=True)
                with m3:
                    st.markdown(f"""
                        <div class="metric-card rank-1">
                            <h3>{avg_score:.1f}%</h3>
                            <p>Average Match Score</p>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Results table
                medals = ["🥇", "🥈", "🥉"]
                for i, (name, score) in enumerate(results):
                    pct = score * 100
                    medal = medals[i] if i < 3 else f"#{i+1}"
                    bar_color = "#667eea" if i == 0 else "#a0aec0"
                    st.markdown(f"""
                        <div class="result-row">
                            <div style="font-size:1.5rem; width:50px">{medal}</div>
                            <div style="flex:1">
                                <div style="font-weight:600; font-size:1rem; color:#2d3748">{name}</div>
                                <div style="background:#e2e8f0; border-radius:999px; height:8px; margin-top:6px">
                                    <div style="background:{bar_color}; width:{pct:.1f}%; height:8px; border-radius:999px"></div>
                                </div>
                            </div>
                            <div style="margin-left:1rem; font-size:1.2rem; font-weight:700; color:#667eea; min-width:60px; text-align:right">{pct:.1f}%</div>
                        </div>
                    """, unsafe_allow_html=True)