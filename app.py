import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import Counter
from datetime import datetime
from fpdf import FPDF
from resume_parser import extract_text_from_pdf
from nlp_engine import rank_resumes

st.set_page_config(page_title="Resume Screener", page_icon="📄", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f6fb; }

    /* ── Sidebar ── */
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

    /* ── Header ── */
    .title-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.2rem 2rem; border-radius: 16px;
        margin-bottom: 2rem; text-align: center;
        box-shadow: 0 4px 20px rgba(102,126,234,0.3);
    }
    .title-container h1 { color: white !important; font-size: 2.4rem; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
    .title-container p  { color: rgba(255,255,255,0.82); font-size: 1.05rem; margin-top: 0.4rem; }

    /* ── Empty state ── */
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

    /* ── Metric cards ── */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px; padding: 1.3rem;
        text-align: center; color: white;
        box-shadow: 0 3px 12px rgba(102,126,234,0.25);
    }
    .metric-card h3 { font-size: 2rem; font-weight: 800; margin: 0; }
    .metric-card p  { font-size: 0.82rem; opacity: 0.85; margin: 0.2rem 0 0; }

    /* ── Result cards ── */
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

    /* ── Section headers ── */
    .section-header {
        font-size: 1.25rem; font-weight: 700;
        color: #1a202c; margin: 1.5rem 0 1rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e2e8f0;
    }

    /* ── Upload count ── */
    .upload-count {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 8px; padding: 0.5rem 0.8rem;
        font-size: 0.85rem; margin-top: 0.4rem;
    }

    /* ── Export buttons ── */
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
""", unsafe_allow_html=True)


# ── SIDEBAR ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="text-align:center; padding: 0.5rem 0 1.5rem;">
            <div style="font-size:2.2rem;">📄</div>
            <div style="font-size:1.2rem; font-weight:800; letter-spacing:-0.3px;">Resume Screener</div>
            <div style="font-size:0.78rem; opacity:0.6; margin-top:0.2rem;">NLP-Powered Candidate Ranking</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📋 Job Description")
    job_description = st.text_area(
        label="",
        height=220,
        placeholder="Paste the job description here...",
        label_visibility="collapsed"
    )

    st.markdown("#### 📁 Upload Resumes")
    uploaded_files = st.file_uploader(
        label="",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files:
        st.markdown(f'<div class="upload-count">✅ {len(uploaded_files)} resume(s) ready</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="upload-count">📂 PDF files only — upload multiple</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    screen_btn = st.button("🔍 Screen Resumes", use_container_width=True)

    st.markdown("""
        <div style="margin-top:2rem; padding-top:1.5rem; border-top:1px solid rgba(255,255,255,0.1);
                    font-size:0.75rem; opacity:0.5; text-align:center; line-height:1.6;">
            Built with KeyBERT · Sentence Transformers<br>spaCy · Streamlit
        </div>
    """, unsafe_allow_html=True)


# ── MAIN HEADER ────────────────────────────────────────────────────────
st.markdown("""
    <div class="title-container">
        <h1>📄 Resume Screener</h1>
        <p>Paste a job description, upload resumes, and get instant AI-powered candidate rankings</p>
    </div>
""", unsafe_allow_html=True)


# ── HELPER FUNCTIONS ───────────────────────────────────────────────────
def score_color(pct):
    if pct >= 70:
        return "#22543d", "#c6f6d5", "🟢 Strong Match"
    elif pct >= 40:
        return "#744210", "#fefcbf", "🟡 Partial Match"
    else:
        return "#742a2a", "#fed7d7", "🔴 Weak Match"


def sanitize(text):
    """
    Replace special Unicode characters that Helvetica (fpdf2) cannot encode.
    Covers bullets, dashes, curly quotes, arrows, and any non-latin-1 character.
    This prevents FPDFUnicodeEncodingException when resumes contain
    special formatting characters.
    """
    replacements = {
        '\u2022': '-',    # bullet •
        '\u2023': '-',    # triangle bullet ‣
        '\u25aa': '-',    # small square ▪
        '\u25cf': '-',    # circle ●
        '\u2013': '-',    # en dash –
        '\u2014': '-',    # em dash —
        '\u2018': "'",    # left single quote '
        '\u2019': "'",    # right single quote '
        '\u201c': '"',    # left double quote "
        '\u201d': '"',    # right double quote "
        '\u2026': '...', # ellipsis …
        '\u2192': '->',  # arrow →
        '\u2713': 'v',   # checkmark ✓
        '\u00e9': 'e',   # é
        '\u00e0': 'a',   # à
        '\u00fc': 'u',   # ü
        '\u00f6': 'o',   # ö
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Final safety net — silently drop anything still outside latin-1
    return text.encode('latin-1', errors='ignore').decode('latin-1')


def build_csv(results):
    rows = []
    for i, (name, score, matched, missing, section_scores, boosters, draggers) in enumerate(results):
        rows.append({
            "Rank":                   i + 1,
            "Resume":                 name,
            "Match Score (%)":        round(score * 100, 1),
            "Matched Skills":         ", ".join(sorted(matched)),
            "Missing Skills":         ", ".join(sorted(missing)),
            "Skills Matched":         len(matched),
            "Skills Missing":         len(missing),
            "Skill Match (%)":        round(len(matched) / (len(matched) + len(missing)) * 100, 1) if (matched or missing) else 0,
            "Top Booster":            boosters[0][0] if boosters else "",
            "Top Dragger":            draggers[0][0] if draggers else "",
            "Section - Skills":       section_scores.get("skills", "N/A"),
            "Section - Experience":   section_scores.get("experience", "N/A"),
            "Section - Education":    section_scores.get("education", "N/A"),
            "Section - Projects":     section_scores.get("projects", "N/A"),
        })
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


def build_pdf(results, job_description):
    """
    Build PDF report. Returns (pdf_bytes, None) on success
    or (None, error_message) on failure so the UI can handle
    it gracefully instead of crashing with a red error screen.
    """
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(102, 126, 234)
        pdf.cell(0, 12, "Resume Screener Report", ln=True, align="C")

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%B %d, %Y  %H:%M')}", ln=True, align="C")
        pdf.ln(4)

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(45, 55, 72)
        pdf.cell(0, 8, "Job Description (preview)", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(80, 80, 80)
        snippet = sanitize(job_description[:300].replace("\n", " "))
        if len(job_description) > 300:
            snippet += "..."
        pdf.multi_cell(0, 5, snippet)
        pdf.ln(4)

        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        for i, (name, score, matched, missing, section_scores, boosters, draggers) in enumerate(results):
            pct       = round(score * 100, 1)
            skill_pct = round(len(matched) / (len(matched) + len(missing)) * 100, 1) if (matched or missing) else 0

            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(102, 126, 234)
            pdf.cell(0, 9, sanitize(f"#{i+1}  {name}"), ln=True)

            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(45, 55, 72)
            pdf.cell(0, 6,
                f"Match Score: {pct}%   |   Skill Match: {skill_pct}%   |   "
                f"{len(matched)} matched  /  {len(missing)} missing",
                ln=True
            )

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(21, 87, 36)
            pdf.cell(0, 6, "Matched Skills:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 5, sanitize(", ".join(sorted(matched)) if matched else "None"))

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(114, 28, 36)
            pdf.cell(0, 6, "Missing Skills:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 5, sanitize(", ".join(sorted(missing)) if missing else "None"))

            if section_scores:
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(45, 55, 72)
                pdf.cell(0, 6, "Section Scores:", ln=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(80, 80, 80)
                sec_line = "   ".join([f"{k.title()}: {v}%" for k, v in section_scores.items()])
                pdf.multi_cell(0, 5, sanitize(sec_line))

            pdf.ln(3)
            pdf.set_draw_color(220, 220, 220)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)

        return bytes(pdf.output()), None   # success

    except Exception as e:
        return None, str(e)               # graceful failure


# ── SCREENING ──────────────────────────────────────────────────────────
if screen_btn:
    if not job_description.strip():
        st.warning("⚠️ Please enter a job description in the sidebar.")
    elif not uploaded_files:
        st.warning("⚠️ Please upload at least one resume in the sidebar.")
    else:
        progress_bar = st.progress(0)
        status = st.empty()

        status.markdown("**⏳ Step 1 of 4 — Extracting text from resumes...**")
        progress_bar.progress(10)

        resumes = {}
        failed  = []
        for file in uploaded_files:
            text = extract_text_from_pdf(file)
            if text:
                resumes[file.name] = text
            else:
                failed.append(file.name)

        if failed:
            st.error(f"⚠️ Could not extract text from: {', '.join(failed)}. The file may be scanned/image-based.")

        status.markdown("**⏳ Step 2 of 4 — Analyzing skills with KeyBERT...**")
        progress_bar.progress(35)

        if resumes:
            status.markdown("**⏳ Step 3 of 4 — Ranking candidates semantically...**")
            progress_bar.progress(65)

            st.session_state["results"]         = rank_resumes(job_description, resumes)
            st.session_state["job_description"] = job_description

            status.markdown("**✅ Step 4 of 4 — Done! Results ready.**")
            progress_bar.progress(100)

            import time
            time.sleep(0.6)
            progress_bar.empty()
            status.empty()


# ── EMPTY STATE ────────────────────────────────────────────────────────
if "results" not in st.session_state or not st.session_state["results"]:
    st.markdown("""
        <div class="empty-state">
            <div class="icon">🎯</div>
            <h2>Ready to Screen Candidates</h2>
            <p>Paste a job description and upload resumes in the sidebar, then click <strong>Screen Resumes</strong>.</p>
            <div class="empty-steps">
                <div class="step-card">
                    <div class="step-num">1</div>
                    <p>Paste a<br><strong>Job Description</strong></p>
                </div>
                <div class="step-card">
                    <div class="step-num">2</div>
                    <p>Upload<br><strong>PDF Resumes</strong></p>
                </div>
                <div class="step-card">
                    <div class="step-num">3</div>
                    <p>Click<br><strong>Screen Resumes</strong></p>
                </div>
                <div class="step-card">
                    <div class="step-num">4</div>
                    <p>View<br><strong>Ranked Results</strong></p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


# ── RESULTS ────────────────────────────────────────────────────────────
elif "results" in st.session_state and st.session_state["results"]:
    results         = st.session_state["results"]
    job_description = st.session_state["job_description"]

    top_score = results[0][1] * 100 if results else 0
    avg_score = sum(r[1] for r in results) / len(results) * 100 if results else 0

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'<div class="metric-card"><h3>{len(results)}</h3><p>Resumes Screened</p></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><h3>{top_score:.1f}%</h3><p>Top Match Score</p></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><h3>{avg_score:.1f}%</h3><p>Average Match Score</p></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Analytics ─────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📈 Analytics Dashboard</div>', unsafe_allow_html=True)

    dash_col1, dash_col2 = st.columns(2, gap="large")

    with dash_col1:
        st.markdown("**🏅 Candidate Score Distribution**")
        names      = [r[0].replace(".pdf", "") for r in results]
        scores     = [round(r[1] * 100, 1) for r in results]
        bar_colors = ["#667eea" if i == 0 else "#a0aec0" for i in range(len(names))]
        fig_scores = go.Figure(go.Bar(
            x=names, y=scores, marker_color=bar_colors,
            text=[f"{s}%" for s in scores], textposition="outside",
            hovertemplate="<b>%{x}</b><br>Score: %{y}%<extra></extra>",
        ))
        fig_scores.update_layout(
            yaxis=dict(range=[0, 110], title="Match Score (%)", gridcolor="#e2e8f0"),
            xaxis=dict(title=""), plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="sans-serif", size=12, color="#2d3748"),
            margin=dict(t=20, b=40, l=40, r=20), height=300, showlegend=False,
        )
        st.plotly_chart(fig_scores, use_container_width=True)

    with dash_col2:
        st.markdown("**❌ Most Commonly Missing Skills**")
        all_missing = []
        for r in results:
            all_missing.extend(list(r[3]))
        skill_counts = Counter(all_missing).most_common(10)
        if skill_counts:
            skills_list = [s for s, _ in skill_counts]
            counts_list = [c for _, c in skill_counts]
            max_c = max(counts_list)
            bar_colors_missing = [
                f"rgba(229,62,62,{0.4 + 0.6*(c/max_c):.2f})" for c in counts_list
            ]
            fig_missing = go.Figure(go.Bar(
                x=counts_list[::-1], y=skills_list[::-1], orientation="h",
                marker_color=bar_colors_missing[::-1],
                text=[f"{c} resume{'s' if c>1 else ''}" for c in counts_list[::-1]],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Missing in %{x} resume(s)<extra></extra>",
            ))
            fig_missing.update_layout(
                xaxis=dict(title="Resumes Missing Skill", gridcolor="#e2e8f0", range=[0, max_c+1], dtick=1),
                yaxis=dict(title=""), plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="sans-serif", size=11, color="#2d3748"),
                margin=dict(t=20, b=40, l=20, r=60), height=300, showlegend=False,
            )
            st.plotly_chart(fig_missing, use_container_width=True)
        else:
            st.info("No missing skills detected.")

    st.markdown("**🎯 Skill Match Rate per Candidate**")
    match_names, match_pcts, missing_pcts = [], [], []
    for r in results:
        total = len(r[2]) + len(r[3])
        match_names.append(r[0].replace(".pdf", ""))
        match_pcts.append(round(len(r[2]) / total * 100, 1) if total else 0)
        missing_pcts.append(round(len(r[3]) / total * 100, 1) if total else 0)

    fig_stacked = go.Figure()
    fig_stacked.add_trace(go.Bar(
        name="✅ Matched", x=match_names, y=match_pcts, marker_color="#48bb78",
        text=[f"{v}%" for v in match_pcts], textposition="inside",
        hovertemplate="<b>%{x}</b><br>Matched: %{y}%<extra></extra>",
    ))
    fig_stacked.add_trace(go.Bar(
        name="❌ Missing", x=match_names, y=missing_pcts, marker_color="#fc8181",
        text=[f"{v}%" for v in missing_pcts], textposition="inside",
        hovertemplate="<b>%{x}</b><br>Missing: %{y}%<extra></extra>",
    ))
    fig_stacked.update_layout(
        barmode="stack",
        yaxis=dict(title="Skill Coverage (%)", gridcolor="#e2e8f0", range=[0, 110]),
        xaxis=dict(title=""), plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="sans-serif", size=12, color="#2d3748"),
        margin=dict(t=10, b=40, l=40, r=20), height=280,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_stacked, use_container_width=True)

    # ── Export ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">💾 Export Results</div>', unsafe_allow_html=True)

    exp_col1, exp_col2, exp_col3 = st.columns([1, 1, 2])

    with exp_col1:
        st.download_button(
            label="⬇️ Download CSV",
            data=build_csv(results),
            file_name=f"resume_screening_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with exp_col2:
        pdf_bytes, pdf_error = build_pdf(results, job_description)
        if pdf_error:
            # Graceful failure — friendly message instead of red crash screen
            st.button(
                "⚠️ PDF Unavailable",
                disabled=True,
                use_container_width=True,
                help="PDF export failed due to special characters in the resume. Use CSV instead."
            )
            st.caption("⚠️ PDF failed — resume contains special characters. Please use CSV export.")
        else:
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_bytes,
                file_name=f"resume_screening_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    with exp_col3:
        st.caption(
            "📄 **CSV** — full ranked table, open in Excel.\n\n"
            "📋 **PDF** — formatted report to share with hiring managers."
        )

    # ── Detailed Results ───────────────────────────────────────────────
    st.markdown('<div class="section-header">🏆 Detailed Results</div>', unsafe_allow_html=True)

    medals = ["🥇", "🥈", "🥉"]

    for i, (name, score, matched, missing, section_scores, boosters, draggers) in enumerate(results):
        pct       = score * 100
        medal     = medals[i] if i < 3 else f"#{i+1}"
        skill_pct = (len(matched) / (len(matched) + len(missing)) * 100) if (matched or missing) else 0
        txt_color, bg_color, label = score_color(pct)

        with st.container():
            st.markdown(f"""
                <div class="result-card">
                    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:0.6rem;">
                        <div style="display:flex; align-items:center; gap:0.7rem;">
                            <span style="font-size:1.6rem;">{medal}</span>
                            <div>
                                <div class="candidate-name">{name}</div>
                                <div style="font-size:0.78rem; color:#718096; margin-top:1px;">
                                    Skill Match: {skill_pct:.0f}% &nbsp;·&nbsp;
                                    {len(matched)} matched &nbsp;·&nbsp; {len(missing)} missing
                                </div>
                            </div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:1.6rem; font-weight:800; color:{txt_color};">{pct:.1f}%</div>
                            <span style="background:{bg_color}; color:{txt_color}; border-radius:20px;
                                         padding:2px 10px; font-size:0.72rem; font-weight:600;">{label}</span>
                        </div>
                    </div>
                    <div style="background:#e2e8f0; border-radius:999px; height:7px;">
                        <div style="width:{min(pct,100):.1f}%; height:7px; border-radius:999px;
                                    background:linear-gradient(90deg,#667eea,#764ba2);"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            with st.expander(f"👁 View Full Details — {name}"):

                # ── Score Explanation ──────────────────────────────────
                if boosters or draggers:
                    st.markdown("**🔍 Why This Resume Scored This Way**")
                    st.caption("Each keyword from the resume was compared to the JD individually. High = helped. Low = noise.")
                    exp1, exp2 = st.columns(2)
                    with exp1:
                        st.markdown("**🚀 Score Boosters**")
                        for keyword, sim in boosters:
                            bar_w = min(int(sim), 100)
                            color = "#38a169" if sim >= 60 else "#d69e2e"
                            st.markdown(f"""
                                <div style="margin-bottom:7px">
                                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#2d3748; margin-bottom:2px">
                                        <span>🟢 {keyword}</span>
                                        <span style="color:{color}; font-weight:600">{sim:.0f}%</span>
                                    </div>
                                    <div style="background:#e2e8f0; border-radius:999px; height:5px">
                                        <div style="background:{color}; width:{bar_w}%; height:5px; border-radius:999px"></div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                    with exp2:
                        st.markdown("**🧹 Score Draggers**")
                        for keyword, sim in draggers:
                            bar_w = min(int(sim), 100)
                            st.markdown(f"""
                                <div style="margin-bottom:7px">
                                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#2d3748; margin-bottom:2px">
                                        <span>🔴 {keyword}</span>
                                        <span style="color:#e53e3e; font-weight:600">{sim:.0f}%</span>
                                    </div>
                                    <div style="background:#e2e8f0; border-radius:999px; height:5px">
                                        <div style="background:#fc8181; width:{bar_w}%; height:5px; border-radius:999px"></div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

                # ── Section Breakdown ──────────────────────────────────
                if section_scores:
                    st.markdown("**📊 Section Breakdown**")
                    section_labels = {
                        'skills': '🛠 Skills', 'experience': '💼 Experience',
                        'education': '🎓 Education', 'projects': '🚀 Projects',
                        'certifications': '📜 Certifications',
                    }
                    for sec, sec_pct in sorted(section_scores.items(), key=lambda x: x[1], reverse=True):
                        label_sec = section_labels.get(sec, sec.title())
                        bar_w     = min(sec_pct, 100)
                        color     = "#667eea" if sec_pct >= 60 else "#f6ad55" if sec_pct >= 35 else "#fc8181"
                        st.markdown(f"""
                            <div style="margin-bottom:8px">
                                <div style="display:flex; justify-content:space-between; font-size:0.82rem; color:#4a5568; margin-bottom:3px">
                                    <span>{label_sec}</span><span>{sec_pct:.1f}%</span>
                                </div>
                                <div style="background:#e2e8f0; border-radius:999px; height:7px">
                                    <div style="background:{color}; width:{bar_w}%; height:7px; border-radius:999px"></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

                # ── Matched / Missing Skills ───────────────────────────
                sc1, sc2 = st.columns(2)
                with sc1:
                    st.markdown("**✅ Matched Skills**")
                    if matched:
                        st.markdown("".join([
                            f'<span class="skill-pill-matched">{s}</span>'
                            for s in sorted(matched)
                        ]), unsafe_allow_html=True)
                    else:
                        st.markdown("_No skills matched_")
                with sc2:
                    st.markdown("**❌ Missing Skills**")
                    if missing:
                        st.markdown("".join([
                            f'<span class="skill-pill-missing">{s}</span>'
                            for s in sorted(missing)
                        ]), unsafe_allow_html=True)
                    else:
                        st.markdown("_No skills missing — great match!_")