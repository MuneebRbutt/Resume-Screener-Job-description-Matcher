from dataclasses import dataclass

from models import ResumeResult
from nlp_engine import rank_resumes
from resume_parser import extract_text_from_pdf


@dataclass(frozen=True)
class ScreeningOutcome:
    results: list[ResumeResult]
    failed_files: list[str]


def run_screening(job_description: str, uploaded_files) -> ScreeningOutcome:
    resumes = {}
    failed_files = []

    for file in uploaded_files:
        text = extract_text_from_pdf(file)
        if text:
            resumes[file.name] = text
        else:
            failed_files.append(file.name)

    results = rank_resumes(job_description, resumes) if resumes else []
    return ScreeningOutcome(results=results, failed_files=failed_files)
