import spacy
import nltk
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util
from section_parser import parse_sections, SECTION_WEIGHTS

nltk.download('stopwords', quiet=True)

nlp = spacy.load("en_core_web_sm")

kw_model = KeyBERT()
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')


def extract_skills(text):
    """Extract top keywords from text using KeyBERT."""
    try:
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=20,
            use_mmr=True,
            diversity=0.5
        )
        return set(kw.lower().strip() for kw, score in keywords)
    except Exception:
        return set()


def get_skill_match(jd_skills, resume_raw_text):
    """
    Check which JD skills appear in the resume text.
    For multi-word phrases like 'python java', checks each word individually.
    """
    resume_lower = resume_raw_text.lower()
    matched = set()
    missing = set()

    for skill in jd_skills:
        words = skill.lower().split()
        if len(words) == 1:
            if skill.lower() in resume_lower:
                matched.add(skill)
            else:
                missing.add(skill)
        else:
            if all(word in resume_lower for word in words):
                matched.add(skill)
            else:
                missing.add(skill)

    return matched, missing


def compute_weighted_score(job_description, sections):
    """
    Encodes JD and each resume section separately using sentence transformers.
    Computes cosine similarity per section, then returns a weighted final score.

    This is what separates this from basic TF-IDF ATS systems — section-aware
    semantic scoring means a skill in the Skills section counts more than the
    same word appearing in the Objective statement.

    Returns:
        final_score   (float) — weighted combined similarity
        section_scores (dict) — { section_name: similarity_score }
    """
    jd_embedding = embedding_model.encode(job_description, convert_to_tensor=True)

    section_scores = {}
    total_score = 0.0
    total_weight = 0.0

    for section_name, content in sections.items():
        if not content.strip():
            continue

        weight = SECTION_WEIGHTS.get(section_name, 0.0)
        if weight == 0.0:
            continue

        section_embedding = embedding_model.encode(content, convert_to_tensor=True)
        similarity = float(util.cos_sim(jd_embedding, section_embedding)[0][0])

        section_scores[section_name] = round(similarity * 100, 1)  # store as %
        total_score += similarity * weight
        total_weight += weight

    # Normalize in case some sections are missing from the resume
    final_score = (total_score / total_weight) if total_weight > 0 else 0.0
    return final_score, section_scores


def rank_resumes(job_description, resumes: dict):
    """
    Main ranking function.
    Returns list of (filename, score, matched_skills, missing_skills, section_scores)
    sorted by score descending.
    """
    jd_skills = extract_skills(job_description)

    results = []

    for filename, raw_text in resumes.items():
        # Step 1 — Parse resume into sections
        sections = parse_sections(raw_text)

        # Step 2 — Fallback: if no sections detected treat whole text as experience
        if not sections or all(k == 'unknown' for k in sections):
            sections = {'experience': raw_text}

        # Step 3 — Weighted section scoring
        score, section_scores = compute_weighted_score(job_description, sections)

        # Step 4 — Skill gap analysis on full raw text
        matched, missing = get_skill_match(jd_skills, raw_text)

        results.append((filename, score, matched, missing, section_scores))

    results.sort(key=lambda x: x[1], reverse=True)
    return results