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
    """Check which JD skills appear in the resume text."""
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


def explain_score(resume_text, jd_embedding, top_n=5):
    """
    SHAP-inspired keyword attribution.

    For each keyword extracted from the resume:
      - Encode it into a vector
      - Measure its cosine similarity to the JD
      - High similarity  → this keyword HELPED the score (booster)
      - Low similarity   → this keyword HURT the score (dragger/noise)

    Returns:
        boosters : list of (keyword, similarity%) — top contributors
        draggers : list of (keyword, similarity%) — noise keywords
    """
    try:
        keywords = kw_model.extract_keywords(
            resume_text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=30,          # extract more so we have enough to split
            use_mmr=True,
            diversity=0.6
        )
    except Exception:
        return [], []

    if not keywords:
        return [], []

    keyword_texts = [kw for kw, _ in keywords]

    # Encode all keywords in one batch (fast)
    keyword_embeddings = embedding_model.encode(
        keyword_texts,
        convert_to_tensor=True
    )

    # Compare each keyword vector to the JD vector
    similarities = util.cos_sim(jd_embedding, keyword_embeddings)[0]

    # Build scored list
    scored = [
        (keyword_texts[i], float(similarities[i]) * 100)
        for i in range(len(keyword_texts))
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Top N = boosters (helped the score)
    boosters = scored[:top_n]

    # Bottom N = draggers (noise that didn't relate to JD)
    draggers = scored[-(top_n):]
    draggers.reverse()  # worst first

    return boosters, draggers


def compute_weighted_score(job_description, sections, jd_embedding):
    """
    Encodes each resume section separately, computes weighted similarity.
    Returns final_score and per-section scores.
    """
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

        section_scores[section_name] = round(similarity * 100, 1)
        total_score += similarity * weight
        total_weight += weight

    final_score = (total_score / total_weight) if total_weight > 0 else 0.0
    return final_score, section_scores


def rank_resumes(job_description, resumes: dict):
    """
    Main ranking function.
    Returns list of:
    (filename, score, matched_skills, missing_skills, section_scores, boosters, draggers)
    sorted by score descending.
    """
    jd_skills = extract_skills(job_description)

    # Encode JD once — reused for all resumes
    jd_embedding = embedding_model.encode(job_description, convert_to_tensor=True)

    results = []

    for filename, raw_text in resumes.items():

        # Step 1 — Parse resume into sections
        sections = parse_sections(raw_text)
        if not sections or all(k == 'unknown' for k in sections):
            sections = {'experience': raw_text}

        # Step 2 — Weighted section scoring
        score, section_scores = compute_weighted_score(
            job_description, sections, jd_embedding
        )

        # Step 3 — Skill gap analysis
        matched, missing = get_skill_match(jd_skills, raw_text)

        # Step 4 — Score explanation (new)
        boosters, draggers = explain_score(raw_text, jd_embedding)

        results.append((
            filename,
            score,
            matched,
            missing,
            section_scores,
            boosters,    # ← new
            draggers     # ← new
        ))

    results.sort(key=lambda x: x[1], reverse=True)
    return results