import spacy
import nltk
import streamlit as st
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util
from models import ResumeResult
from section_parser import parse_sections, SECTION_WEIGHTS

nltk.download('stopwords', quiet=True)

# ── Load models lazily via Streamlit cache ─────────────────────────
# This prevents the "client has been closed" error caused by loading
# models at import time while Streamlit's async HTTP client is active.

@st.cache_resource
def load_spacy():
    return spacy.load("en_core_web_sm")

@st.cache_resource
def load_keybert():
    return KeyBERT()

@st.cache_resource
def load_sentence_transformer():
    return SentenceTransformer('all-MiniLM-L6-v2')


# Everything below stays exactly the same as before,
# just replace the three module-level variables with function calls:

def preprocess_text(text):
    nlp = load_spacy()
    doc = nlp(text.lower())
    tokens = [
        token.lemma_ for token in doc
        if not token.is_stop and not token.is_punct and token.is_alpha
    ]
    return " ".join(tokens)


def extract_skills(text):
    kw_model = load_keybert()
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
    kw_model = load_keybert()
    embedding_model = load_sentence_transformer()
    try:
        keywords = kw_model.extract_keywords(
            resume_text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=30,
            use_mmr=True,
            diversity=0.6
        )
    except Exception:
        return [], []

    if not keywords:
        return [], []

    keyword_texts = [kw for kw, _ in keywords]
    keyword_embeddings = embedding_model.encode(keyword_texts, convert_to_tensor=True)
    similarities = util.cos_sim(jd_embedding, keyword_embeddings)[0]

    scored = [
        (keyword_texts[i], float(similarities[i]) * 100)
        for i in range(len(keyword_texts))
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    boosters = scored[:top_n]
    draggers = scored[-(top_n):]
    draggers.reverse()

    return boosters, draggers


def compute_weighted_score(job_description, sections, jd_embedding):
    embedding_model = load_sentence_transformer()
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


def rank_resumes(job_description, resumes: dict) -> list[ResumeResult]:
    embedding_model = load_sentence_transformer()
    jd_skills = extract_skills(job_description)
    jd_embedding = embedding_model.encode(job_description, convert_to_tensor=True)

    results = []
    for filename, raw_text in resumes.items():
        sections = parse_sections(raw_text)
        if not sections or all(k == 'unknown' for k in sections):
            sections = {'experience': raw_text}

        score, section_scores = compute_weighted_score(job_description, sections, jd_embedding)
        matched, missing = get_skill_match(jd_skills, raw_text)
        boosters, draggers = explain_score(raw_text, jd_embedding)

        results.append(
            ResumeResult(
                filename=filename,
                score=score,
                matched_skills=matched,
                missing_skills=missing,
                section_scores=section_scores,
                boosters=boosters,
                draggers=draggers,
            )
        )

    results.sort(key=lambda result: result.score, reverse=True)
    return results
