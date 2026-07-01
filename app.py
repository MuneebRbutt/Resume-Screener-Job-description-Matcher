import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
from io import BytesIO
from datetime import datetime
from fpdf import FPDF
from resume_parser import extract_text_from_pdf
from nlp_engine import rank_resumes

st.set_page_config(page_title="Resume Screener", page_icon="📄", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stApp { max-width: 1200px; margin: 0 auto; }
    .title-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem; border-radius: 15px;
        margin-bottom: 2rem; text-align: center;
    }
    .title-container h1 { color: white !important; font-size: 2.5rem; font-weight: 700; margin: 0; }
    .title-container p { color: rgba(255,255,255,0.85); font-size: 1.1rem; margin-top: 0.5rem; }
    .section-title {
        font-size: 1.1rem; font-weight: 600; color: #495057;
        margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px; padding: 1.2rem; text-align: center; color: white;
    }
    .metric-card h3 { font-size: 2rem; font-weight: 700; margin: 0; }
    .metric-card p { font-size: 0.85rem; opacity: 0.85; margin: 0; }
    .result-row {
        display: flex; align-items: center; padding: 1rem 1.2rem;
        border-radius: 10px; margin-bottom: 0.8rem; background: white;
        border: 1px solid #e9ecef; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; border-radius: 8px;
        padding: 0.6rem 2rem; font-size: 1rem; font-weight: 600;
        width: 100%; transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.9; color: white; }
    .stTextArea textarea { border-radius: 8px; border: 1px solid #dee2e6; font-size: 0.95rem; }
    .upload-count {
        background: #e8f4fd; border: 1px solid #bee3f8; border-radius: 8px;
        padding: 0.6rem 1rem; color: #2b6cb0; font-size: 0.9rem;
        font-weight: 500; margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="title-container">
        <h1>📄 Resume Screener</h1>
        <p>Upload a job description and resumes to instantly find the best candidates</p>
    </div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1.2, 1], gap="large")

with col1:
    st.markdown('<div class="section-title">📋 Job Description</div>', unsafe_allow_html=True)
    job_description = st.text_area(
        label="", height=280,
        placeholder="Paste the job description here...",
        label_visibility="collapsed"
    )

with col2:
    st.markdown('<div class="section-title">📁 Upload Resumes</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        label="", type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    if uploaded_files:
        st.markdown(f'<div class="upload-count">✅ {len(uploaded_files)} resume(s) uploaded and ready</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="upload-count">📂 No resumes uploaded yet — supports PDF only</div>', unsafe_allow_html=True)

_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    screen_btn = st.button("🔍 Screen Resumes")

# ── SESSION STATE: run screening only when button clicked ──────────────
# Storing results in session_state means they survive download button
# reruns — without this, clicking Download CSV wipes the results page.
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
                # Store everything in session_state so reruns keep it
                st.session_state["results"]         = rank_resumes(job_description, resumes)
                st.session_state["job_description"] = job_description


# ── RENDER RESULTS (reads from session_state, survives reruns) ─────────
if "results" in st.session_state and st.session_state["results"]:
    results         = st.session_state["results"]
    job_description = st.session_state["job_description"]

    # ── Export helper functions ────────────────────────────────────────
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
        df = pd.DataFrame(rows)
        return df.to_csv(index=False).encode("utf-8")

    def build_pdf(results, job_description):
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
        snippet = job_description[:300].replace("\n", " ") + ("..." if len(job_description) > 300 else "")
        pdf.multi_cell(0, 5, snippet)
        pdf.ln(4)

        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        medals_txt = ["#1", "#2", "#3"]
        for i, (name, score, matched, missing, section_scores, boosters, draggers) in enumerate(results):
            pct       = round(score * 100, 1)
            rank_tag  = medals_txt[i] if i < 3 else f"#{i+1}"
            skill_pct = round(len(matched) / (len(matched) + len(missing)) * 100, 1) if (matched or missing) else 0

            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(102, 126, 234)
            pdf.cell(0, 9, f"{rank_tag}  {name}", ln=True)

            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(45, 55, 72)
            pdf.cell(0, 6, f"Match Score: {pct}%   |   Skill Match: {skill_pct}%   |   {len(matched)} matched  /  {len(missing)} missing", ln=True)

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(21, 87, 36)
            pdf.cell(0, 6, "Matched Skills:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 5, ", ".join(sorted(matched)) if matched else "None")

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(114, 28, 36)
            pdf.cell(0, 6, "Missing Skills:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 5, ", ".join(sorted(missing)) if missing else "None")

            if section_scores:
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(45, 55, 72)
                pdf.cell(0, 6, "Section Scores:", ln=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(80, 80, 80)
                sec_line = "   ".join([f"{k.title()}: {v}%" for k, v in section_scores.items()])
                pdf.multi_cell(0, 5, sec_line)

            pdf.ln(3)
            pdf.set_draw_color(220, 220, 220)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)

        return bytes(pdf.output())

    # ── Summary Metrics ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 🏆 Results")

    m1, m2, m3 = st.columns(3)
    top_score = results[0][1] * 100 if results else 0
    avg_score = sum(r[1] for r in results) / len(results) * 100 if results else 0

    with m1:
        st.markdown(f'<div class="metric-card"><h3>{len(results)}</h3><p>Resumes Screened</p></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><h3>{top_score:.1f}%</h3><p>Top Match Score</p></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><h3>{avg_score:.1f}%</h3><p>Average Match Score</p></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── FEATURE 5: ANALYTICS DASHBOARD ────────────────────────────────
    st.markdown("## 📈 Analytics Dashboard")

    dash_col1, dash_col2 = st.columns(2, gap="large")

    with dash_col1:
        st.markdown("**🏅 Candidate Score Distribution**")
        names  = [r[0].replace(".pdf", "") for r in results]
        scores = [round(r[1] * 100, 1) for r in results]
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
            margin=dict(t=20, b=40, l=40, r=20), height=320, showlegend=False,
        )
        st.plotly_chart(fig_scores, use_container_width=True)

    with dash_col2:
        st.markdown("**❌ Most Commonly Missing Skills Across All Resumes**")
        all_missing = []
        for r in results:
            all_missing.extend(list(r[3]))
        skill_counts = Counter(all_missing).most_common(10)

        if skill_counts:
            skills_list = [s for s, _ in skill_counts]
            counts_list = [c for _, c in skill_counts]
            max_c = max(counts_list)
            bar_colors_missing = [
                f"rgba(229, 62, 62, {0.4 + 0.6 * (c / max_c):.2f})" for c in counts_list
            ]
            fig_missing = go.Figure(go.Bar(
                x=counts_list[::-1], y=skills_list[::-1], orientation="h",
                marker_color=bar_colors_missing[::-1],
                text=[f"{c} resume{'s' if c > 1 else ''}" for c in counts_list[::-1]],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Missing in %{x} resume(s)<extra></extra>",
            ))
            fig_missing.update_layout(
                xaxis=dict(title="Number of Resumes Missing This Skill", gridcolor="#e2e8f0", range=[0, max_c + 1], dtick=1),
                yaxis=dict(title=""), plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="sans-serif", size=11, color="#2d3748"),
                margin=dict(t=20, b=40, l=20, r=60), height=320, showlegend=False,
            )
            st.plotly_chart(fig_missing, use_container_width=True)
        else:
            st.info("No missing skills detected across resumes.")

    st.markdown("**🎯 Skill Match Rate per Candidate**")
    match_names  = [r[0].replace(".pdf", "") for r in results]
    match_pcts   = []
    missing_pcts = []
    for r in results:
        matched_n = len(r[2])
        missing_n = len(r[3])
        total     = matched_n + missing_n
        match_pcts.append(round(matched_n / total * 100, 1) if total else 0)
        missing_pcts.append(round(missing_n / total * 100, 1) if total else 0)

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
        margin=dict(t=10, b=40, l=40, r=20), height=300,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_stacked, use_container_width=True)

    # ── FEATURE 6: EXPORT ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 💾 Export Results")

    exp_col1, exp_col2, exp_col3 = st.columns([1, 1, 2])

    with exp_col1:
        csv_bytes = build_csv(results)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_bytes,
            file_name=f"resume_screening_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with exp_col2:
        pdf_bytes = build_pdf(results, job_description)
        st.download_button(
            label="⬇️ Download PDF Report",
            data=pdf_bytes,
            file_name=f"resume_screening_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with exp_col3:
        st.caption("📄 **CSV** — ranked table with all scores, matched & missing skills, section breakdown. Open in Excel.\n\n📋 **PDF** — formatted report with full details per candidate. Share with hiring managers.")

    # ── DETAILED RESULTS ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 🏆 Detailed Results")

    medals = ["🥇", "🥈", "🥉"]

    for i, (name, score, matched, missing, section_scores, boosters, draggers) in enumerate(results):
        pct       = score * 100
        medal     = medals[i] if i < 3 else f"#{i+1}"
        bar_color = "#667eea" if i == 0 else "#a0aec0"
        skill_pct = (len(matched) / (len(matched) + len(missing)) * 100) if (matched or missing) else 0

        st.markdown(f"""
            <div class="result-row">
                <div style="font-size:1.5rem; width:50px">{medal}</div>
                <div style="flex:1">
                    <div style="font-weight:600; font-size:1rem; color:#2d3748">{name}</div>
                    <div style="background:#e2e8f0; border-radius:999px; height:8px; margin-top:6px">
                        <div style="background:{bar_color}; width:{pct:.1f}%; height:8px; border-radius:999px"></div>
                    </div>
                    <div style="font-size:0.78rem; color:#718096; margin-top:4px">
                        Skill Match: {skill_pct:.0f}% &nbsp;|&nbsp; {len(matched)} matched &nbsp;|&nbsp; {len(missing)} missing
                    </div>
                </div>
                <div style="margin-left:1rem; font-size:1.2rem; font-weight:700; color:#667eea; min-width:60px; text-align:right">{pct:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)

        with st.expander(f"👁 View Skill Details — {name}"):

            # ── FEATURE 4: SCORE EXPLANATION ──────────────────────────
            if boosters or draggers:
                st.markdown("**🔍 Why This Resume Scored This Way**")
                st.caption("Each keyword from the resume was compared to the job description individually. High similarity = helped the score. Low similarity = noise that dragged the score down.")

                exp1, exp2 = st.columns(2)

                with exp1:
                    st.markdown("**🚀 Score Boosters** *(keywords that helped)*")
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
                    st.markdown("**🧹 Score Draggers** *(noise — unrelated to JD)*")
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

            # ── SECTION BREAKDOWN ──────────────────────────────────────
            if section_scores:
                st.markdown("**📊 Section Breakdown** *(how each part of the resume scored)*")
                section_labels = {
                    'skills': '🛠 Skills', 'experience': '💼 Experience',
                    'education': '🎓 Education', 'projects': '🚀 Projects',
                    'certifications': '📜 Certifications',
                }
                for sec, sec_pct in sorted(section_scores.items(), key=lambda x: x[1], reverse=True):
                    label = section_labels.get(sec, sec.title())
                    bar_w = min(sec_pct, 100)
                    color = "#667eea" if sec_pct >= 60 else "#f6ad55" if sec_pct >= 35 else "#fc8181"
                    st.markdown(f"""
                        <div style="margin-bottom:8px">
                            <div style="display:flex; justify-content:space-between; font-size:0.82rem; color:#4a5568; margin-bottom:3px">
                                <span>{label}</span><span>{sec_pct:.1f}%</span>
                            </div>
                            <div style="background:#e2e8f0; border-radius:999px; height:7px">
                                <div style="background:{color}; width:{bar_w}%; height:7px; border-radius:999px"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

            # ── MATCHED / MISSING SKILLS ───────────────────────────────
            sc1, sc2 = st.columns(2)

            with sc1:
                st.markdown("**✅ Matched Skills**")
                if matched:
                    skills_html = "".join([
                        f'<span style="display:inline-block; background:#d4edda; color:#155724; border-radius:20px; padding:3px 10px; font-size:0.78rem; font-weight:500; margin:3px">{s}</span>'
                        for s in sorted(matched)
                    ])
                    st.markdown(skills_html, unsafe_allow_html=True)
                else:
                    st.markdown("_No skills matched_")

            with sc2:
                st.markdown("**❌ Missing Skills**")
                if missing:
                    skills_html = "".join([
                        f'<span style="display:inline-block; background:#f8d7da; color:#721c24; border-radius:20px; padding:3px 10px; font-size:0.78rem; font-weight:500; margin:3px">{s}</span>'
                        for s in sorted(missing)
                    ])
                    st.markdown(skills_html, unsafe_allow_html=True)
                else:
                    st.markdown("_No skills missing — great match!_")