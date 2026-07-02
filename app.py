import time

import streamlit as st

from services.screening import run_screening
from services.validation import is_probably_job_description
from ui.results import render_empty_state, render_results_dashboard
from ui.sidebar import render_sidebar
from ui.styles import apply_app_styles, render_main_header, render_scoring_expander


st.set_page_config(page_title="Resume Screener", page_icon="📄", layout="wide")


def handle_screening(job_description: str, uploaded_files: list) -> None:
    if not job_description.strip():
        st.warning("⚠️ Please enter a job description in the sidebar.")
        return

    is_valid, reason = is_probably_job_description(job_description)
    if not is_valid:
        st.error(
            f"❌ This doesn't look like a real job description — {reason}. "
            "Please paste an actual job posting."
        )
        return

    if not uploaded_files:
        st.warning("⚠️ Please upload at least one resume in the sidebar.")
        return

    progress_bar = st.progress(0)
    status = st.empty()

    status.markdown("**⏳ Step 1 of 4 — Extracting text from resumes...**")
    progress_bar.progress(10)

    outcome = run_screening(job_description, uploaded_files)

    if outcome.failed_files:
        st.error(
            f"⚠️ Could not extract text from: {', '.join(outcome.failed_files)}. "
            "The file may be scanned/image-based."
        )

    status.markdown("**⏳ Step 2 of 4 — Analyzing skills with KeyBERT...**")
    progress_bar.progress(35)

    if not outcome.results:
        progress_bar.empty()
        status.empty()
        return

    status.markdown("**⏳ Step 3 of 4 — Ranking candidates semantically...**")
    progress_bar.progress(65)

    st.session_state["results"] = outcome.results
    st.session_state["job_description"] = job_description

    status.markdown("**✅ Step 4 of 4 — Done! Results ready.**")
    progress_bar.progress(100)
    time.sleep(0.6)
    progress_bar.empty()
    status.empty()


def main() -> None:
    apply_app_styles()

    job_description, uploaded_files, screen_btn = render_sidebar()
    render_main_header()
    render_scoring_expander()

    if screen_btn:
        handle_screening(job_description, uploaded_files)

    results = st.session_state.get("results", [])
    if not results:
        render_empty_state()
        return

    render_results_dashboard(results, st.session_state["job_description"])


if __name__ == "__main__":
    main()
