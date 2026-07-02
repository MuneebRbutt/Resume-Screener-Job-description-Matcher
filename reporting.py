from datetime import datetime

import pandas as pd
from fpdf import FPDF

from models import ResumeResult


def sanitize(text: str) -> str:
    """
    Replace special Unicode characters that Helvetica (fpdf2) cannot encode.
    """
    replacements = {
        "\u2022": "-",
        "\u2023": "-",
        "\u25aa": "-",
        "\u25cf": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u2192": "->",
        "\u2713": "v",
        "\u00e9": "e",
        "\u00e0": "a",
        "\u00fc": "u",
        "\u00f6": "o",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)

    return text.encode("latin-1", errors="ignore").decode("latin-1")


def build_csv(results: list[ResumeResult]) -> bytes:
    rows = []
    for rank, result in enumerate(results, start=1):
        rows.append(
            {
                "Rank": rank,
                "Resume": result.filename,
                "Match Score (%)": round(result.score_pct, 1),
                "Matched Skills": ", ".join(sorted(result.matched_skills)),
                "Missing Skills": ", ".join(sorted(result.missing_skills)),
                "Skills Matched": len(result.matched_skills),
                "Skills Missing": len(result.missing_skills),
                "Skill Match (%)": round(result.skill_match_pct, 1),
                "Top Booster": result.boosters[0][0] if result.boosters else "",
                "Top Dragger": result.draggers[0][0] if result.draggers else "",
                "Section - Skills": result.section_scores.get("skills", "N/A"),
                "Section - Experience": result.section_scores.get("experience", "N/A"),
                "Section - Education": result.section_scores.get("education", "N/A"),
                "Section - Projects": result.section_scores.get("projects", "N/A"),
            }
        )

    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


def build_pdf(results: list[ResumeResult], job_description: str) -> tuple[bytes | None, str | None]:
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

        for rank, result in enumerate(results, start=1):
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(102, 126, 234)
            pdf.cell(0, 9, sanitize(f"#{rank}  {result.filename}"), ln=True)

            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(45, 55, 72)
            pdf.cell(
                0,
                6,
                (
                    f"Match Score: {result.score_pct:.1f}%   |   "
                    f"Skill Match: {result.skill_match_pct:.1f}%   |   "
                    f"{len(result.matched_skills)} matched  /  {len(result.missing_skills)} missing"
                ),
                ln=True,
            )

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(21, 87, 36)
            pdf.cell(0, 6, "Matched Skills:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(
                0,
                5,
                sanitize(", ".join(sorted(result.matched_skills)) if result.matched_skills else "None"),
            )

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(114, 28, 36)
            pdf.cell(0, 6, "Missing Skills:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(
                0,
                5,
                sanitize(", ".join(sorted(result.missing_skills)) if result.missing_skills else "None"),
            )

            if result.section_scores:
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(45, 55, 72)
                pdf.cell(0, 6, "Section Scores:", ln=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(80, 80, 80)
                sec_line = "   ".join(
                    [f"{section.title()}: {score}%" for section, score in result.section_scores.items()]
                )
                pdf.multi_cell(0, 5, sanitize(sec_line))

            pdf.ln(3)
            pdf.set_draw_color(220, 220, 220)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)

        return bytes(pdf.output()), None
    except Exception as exc:
        return None, str(exc)
