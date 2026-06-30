import spacy
import nltk
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util

nltk.download('stopwords', quiet=True)

nlp = spacy.load("en_core_web_sm")

# Load models once at module level
kw_model = KeyBERT()
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # fast + accurate


def extract_skills(text):
    """
    Extract skills/keywords from text using KeyBERT.
    Returns a set of skill strings.
    """
    try:
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=20,
            use_mmr=True,
            diversity=0.5
        )
        skills = set(kw.lower().strip() for kw, score in keywords)
        return skills
    except Exception:
        return set()


def get_skill_match(jd_skills, resume_raw_text):
    """
    For single-word skills: check if the word exists in resume.
    For multi-word phrases: check if ALL individual words exist in resume.
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


def rank_resumes(job_description, resumes: dict):
    """
    job_description: raw string of JD
    resumes: dict of {filename: raw_text}
    returns: list of (filename, similarity_score, matched_skills, missing_skills)
    sorted by similarity_score descending
    """
    # Extract skills from JD only
    jd_skills = extract_skills(job_description)

    # --- SENTENCE EMBEDDINGS (replaces TF-IDF) ---
    # Encode JD and all resumes into semantic vectors
    jd_embedding = embedding_model.encode(job_description, convert_to_tensor=True)

    filenames = list(resumes.keys())
    resume_texts = list(resumes.values())

    resume_embeddings = embedding_model.encode(resume_texts, convert_to_tensor=True)

    # Cosine similarity between JD and each resume
    scores = util.cos_sim(jd_embedding, resume_embeddings)[0]

    # Build results
    results = []
    for i, filename in enumerate(filenames):
        matched, missing = get_skill_match(jd_skills, resumes[filename])
        results.append((
            filename,
            float(scores[i]),   # convert tensor to plain float
            matched,
            missing
        ))

    results.sort(key=lambda x: x[1], reverse=True)
    return results