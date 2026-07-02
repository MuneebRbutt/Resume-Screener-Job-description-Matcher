import streamlit as st


def render_sidebar() -> tuple[str, list, bool]:
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center; padding: 0.5rem 0 1.5rem;">
                <div style="font-size:2.2rem;">📄</div>
                <div style="font-size:1.2rem; font-weight:800; letter-spacing:-0.3px;">Resume Screener</div>
                <div style="font-size:0.78rem; opacity:0.6; margin-top:0.2rem;">NLP-Powered Candidate Ranking</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### 📋 Job Description")
        job_description = st.text_area(
            label="Job description",
            height=220,
            placeholder="Paste the job description here...",
            label_visibility="collapsed",
        )

        st.markdown("#### 📁 Upload Resumes")
        uploaded_files = st.file_uploader(
            label="Upload resumes",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

        if uploaded_files:
            st.markdown(
                f'<div class="upload-count">✅ {len(uploaded_files)} resume(s) ready</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="upload-count">📂 PDF files only — upload multiple</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        screen_btn = st.button("🔍 Screen Resumes", use_container_width=True)

        st.markdown(
            """
            <div style="margin-top:2rem; padding-top:1.5rem; border-top:1px solid rgba(255,255,255,0.1);
                        font-size:0.75rem; opacity:0.5; text-align:center; line-height:1.6;">
                Built with KeyBERT · Sentence Transformers<br>spaCy · Streamlit
            </div>
            """,
            unsafe_allow_html=True,
        )

    return job_description, uploaded_files or [], screen_btn
