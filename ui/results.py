from collections import Counter
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from models import ResumeResult
from reporting import build_csv, build_pdf


def score_color(pct: float) -> tuple[str, str, str]:
    if pct >= 70:
        return "#22543d", "#c6f6d5", "🟢 Strong Match"
    if pct >= 40:
        return "#744210", "#fefcbf", "🟡 Partial Match"
    return "#742a2a", "#fed7d7", "🔴 Weak Match"


def render_empty_state() -> None:
    st.markdown(
        """
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
        """,
        unsafe_allow_html=True,
    )


def render_results_dashboard(results: list[ResumeResult], job_description: str) -> None:
    top_score = results[0].score_pct if results else 0
    avg_score = sum(result.score for result in results) / len(results) * 100 if results else 0

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            f'<div class="metric-card"><h3>{len(results)}</h3><p>Resumes Screened</p></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="metric-card"><h3>{top_score:.1f}%</h3><p>Top Match Score</p></div>',
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f'<div class="metric-card"><h3>{avg_score:.1f}%</h3><p>Average Match Score</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    render_analytics(results)
    render_export_section(results, job_description)
    render_detailed_results(results)


def render_analytics(results: list[ResumeResult]) -> None:
    st.markdown('<div class="section-header">📈 Analytics Dashboard</div>', unsafe_allow_html=True)

    dash_col1, dash_col2 = st.columns(2, gap="large")

    with dash_col1:
        st.markdown("**🏅 Candidate Score Distribution**")
        names = [result.display_name for result in results]
        scores = [round(result.score_pct, 1) for result in results]
        bar_colors = ["#667eea" if index == 0 else "#a0aec0" for index in range(len(names))]
        fig_scores = go.Figure(
            go.Bar(
                x=names,
                y=scores,
                marker_color=bar_colors,
                text=[f"{score}%" for score in scores],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Score: %{y}%<extra></extra>",
            )
        )
        fig_scores.update_layout(
            yaxis=dict(range=[0, 110], title="Match Score (%)", gridcolor="#e2e8f0"),
            xaxis=dict(title=""),
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="sans-serif", size=12, color="#2d3748"),
            margin=dict(t=20, b=40, l=40, r=20),
            height=300,
            showlegend=False,
        )
        st.plotly_chart(fig_scores, use_container_width=True)

    with dash_col2:
        st.markdown("**❌ Most Commonly Missing Skills**")
        all_missing = []
        for result in results:
            all_missing.extend(list(result.missing_skills))

        skill_counts = Counter(all_missing).most_common(10)
        if skill_counts:
            skills_list = [skill for skill, _ in skill_counts]
            counts_list = [count for _, count in skill_counts]
            max_count = max(counts_list)
            bar_colors_missing = [
                f"rgba(229,62,62,{0.4 + 0.6 * (count / max_count):.2f})"
                for count in counts_list
            ]
            fig_missing = go.Figure(
                go.Bar(
                    x=counts_list[::-1],
                    y=skills_list[::-1],
                    orientation="h",
                    marker_color=bar_colors_missing[::-1],
                    text=[f"{count} resume{'s' if count > 1 else ''}" for count in counts_list[::-1]],
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>Missing in %{x} resume(s)<extra></extra>",
                )
            )
            fig_missing.update_layout(
                xaxis=dict(
                    title="Resumes Missing Skill",
                    gridcolor="#e2e8f0",
                    range=[0, max_count + 1],
                    dtick=1,
                ),
                yaxis=dict(title=""),
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="sans-serif", size=11, color="#2d3748"),
                margin=dict(t=20, b=40, l=20, r=60),
                height=300,
                showlegend=False,
            )
            st.plotly_chart(fig_missing, use_container_width=True)
        else:
            st.info("No missing skills detected.")

    st.markdown("**🎯 Skill Match Rate per Candidate**")
    match_names = [result.display_name for result in results]
    match_pcts = [round(result.skill_match_pct, 1) for result in results]
    missing_pcts = [round(100 - result.skill_match_pct, 1) if (result.matched_skills or result.missing_skills) else 0 for result in results]

    fig_stacked = go.Figure()
    fig_stacked.add_trace(
        go.Bar(
            name="✅ Matched",
            x=match_names,
            y=match_pcts,
            marker_color="#48bb78",
            text=[f"{value}%" for value in match_pcts],
            textposition="inside",
            hovertemplate="<b>%{x}</b><br>Matched: %{y}%<extra></extra>",
        )
    )
    fig_stacked.add_trace(
        go.Bar(
            name="❌ Missing",
            x=match_names,
            y=missing_pcts,
            marker_color="#fc8181",
            text=[f"{value}%" for value in missing_pcts],
            textposition="inside",
            hovertemplate="<b>%{x}</b><br>Missing: %{y}%<extra></extra>",
        )
    )
    fig_stacked.update_layout(
        barmode="stack",
        yaxis=dict(title="Skill Coverage (%)", gridcolor="#e2e8f0", range=[0, 110]),
        xaxis=dict(title=""),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="sans-serif", size=12, color="#2d3748"),
        margin=dict(t=10, b=40, l=40, r=20),
        height=280,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_stacked, use_container_width=True)


def render_export_section(results: list[ResumeResult], job_description: str) -> None:
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
            st.button(
                "⚠️ PDF Unavailable",
                disabled=True,
                use_container_width=True,
                help="PDF export failed due to special characters in the resume. Use CSV instead.",
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


def render_detailed_results(results: list[ResumeResult]) -> None:
    st.markdown('<div class="section-header">🏆 Detailed Results</div>', unsafe_allow_html=True)

    medals = ["🥇", "🥈", "🥉"]
    section_labels = {
        "skills": "🛠 Skills",
        "experience": "💼 Experience",
        "education": "🎓 Education",
        "projects": "🚀 Projects",
        "certifications": "📜 Certifications",
    }

    for index, result in enumerate(results):
        medal = medals[index] if index < 3 else f"#{index + 1}"
        txt_color, bg_color, label = score_color(result.score_pct)

        with st.container():
            st.markdown(
                f"""
                <div class="result-card">
                    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:0.6rem;">
                        <div style="display:flex; align-items:center; gap:0.7rem;">
                            <span style="font-size:1.6rem;">{medal}</span>
                            <div>
                                <div class="candidate-name">{result.filename}</div>
                                <div style="font-size:0.78rem; color:#718096; margin-top:1px;">
                                    Skill Match: {result.skill_match_pct:.0f}% &nbsp;·&nbsp;
                                    {len(result.matched_skills)} matched &nbsp;·&nbsp; {len(result.missing_skills)} missing
                                </div>
                            </div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:1.6rem; font-weight:800; color:{txt_color};">{result.score_pct:.1f}%</div>
                            <span style="background:{bg_color}; color:{txt_color}; border-radius:20px;
                                         padding:2px 10px; font-size:0.72rem; font-weight:600;">{label}</span>
                        </div>
                    </div>
                    <div style="background:#e2e8f0; border-radius:999px; height:7px;">
                        <div style="width:{min(result.score_pct, 100):.1f}%; height:7px; border-radius:999px;
                                    background:linear-gradient(90deg,#667eea,#764ba2);"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander(f"👁 View Full Details — {result.filename}"):
                if result.boosters or result.draggers:
                    st.markdown("**🔍 Why This Resume Scored This Way**")
                    st.caption("Each keyword from the resume was compared to the JD individually. High = helped. Low = noise.")
                    exp1, exp2 = st.columns(2)
                    with exp1:
                        st.markdown("**🚀 Score Boosters**")
                        for keyword, similarity in result.boosters:
                            bar_w = min(int(similarity), 100)
                            color = "#38a169" if similarity >= 60 else "#d69e2e"
                            st.markdown(
                                f"""
                                <div style="margin-bottom:7px">
                                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#2d3748; margin-bottom:2px">
                                        <span>🟢 {keyword}</span>
                                        <span style="color:{color}; font-weight:600">{similarity:.0f}%</span>
                                    </div>
                                    <div style="background:#e2e8f0; border-radius:999px; height:5px">
                                        <div style="background:{color}; width:{bar_w}%; height:5px; border-radius:999px"></div>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                    with exp2:
                        st.markdown("**🧹 Score Draggers**")
                        for keyword, similarity in result.draggers:
                            bar_w = min(int(similarity), 100)
                            st.markdown(
                                f"""
                                <div style="margin-bottom:7px">
                                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#2d3748; margin-bottom:2px">
                                        <span>🔴 {keyword}</span>
                                        <span style="color:#e53e3e; font-weight:600">{similarity:.0f}%</span>
                                    </div>
                                    <div style="background:#e2e8f0; border-radius:999px; height:5px">
                                        <div style="background:#fc8181; width:{bar_w}%; height:5px; border-radius:999px"></div>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                    st.markdown("<br>", unsafe_allow_html=True)

                if result.section_scores:
                    st.markdown("**📊 Section Breakdown**")
                    for section, score in sorted(result.section_scores.items(), key=lambda item: item[1], reverse=True):
                        label_sec = section_labels.get(section, section.title())
                        bar_w = min(score, 100)
                        color = "#667eea" if score >= 60 else "#f6ad55" if score >= 35 else "#fc8181"
                        st.markdown(
                            f"""
                            <div style="margin-bottom:8px">
                                <div style="display:flex; justify-content:space-between; font-size:0.82rem; color:#4a5568; margin-bottom:3px">
                                    <span>{label_sec}</span><span>{score:.1f}%</span>
                                </div>
                                <div style="background:#e2e8f0; border-radius:999px; height:7px">
                                    <div style="background:{color}; width:{bar_w}%; height:7px; border-radius:999px"></div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    st.markdown("<br>", unsafe_allow_html=True)

                sc1, sc2 = st.columns(2)
                with sc1:
                    st.markdown("**✅ Matched Skills**")
                    if result.matched_skills:
                        st.markdown(
                            "".join(
                                f'<span class="skill-pill-matched">{skill}</span>'
                                for skill in sorted(result.matched_skills)
                            ),
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown("_No skills matched_")
                with sc2:
                    st.markdown("**❌ Missing Skills**")
                    if result.missing_skills:
                        st.markdown(
                            "".join(
                                f'<span class="skill-pill-missing">{skill}</span>'
                                for skill in sorted(result.missing_skills)
                            ),
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown("_No skills missing — great match!_")
