import spacy
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from keybert import KeyBERT

nltk.download('stopwords', quiet=True)

nlp = spacy.load("en_core_web_sm")

# Load KeyBERT once at module level
kw_model = KeyBERT()


def preprocess_text(text):
    """Clean and lemmatize text for TF-IDF."""
    doc = nlp(text.lower())
    tokens = [
        token.lemma_ for token in doc
        if not token.is_stop and not token.is_punct and token.is_alpha
    ]
    return " ".join(tokens)


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
    For multi-word phrases (bigrams like 'python java'):
    check if ALL individual words exist in resume — since KeyBERT
    joins related words as phrases but they appear separately in text.
    """
    resume_lower = resume_raw_text.lower()
    matched = set()
    missing = set()

    for skill in jd_skills:
        words = skill.lower().split()

        if len(words) == 1:
            # e.g. "python" → check directly
            if skill.lower() in resume_lower:
                matched.add(skill)
            else:
                missing.add(skill)
        else:
            # e.g. "python java" → check if "python" AND "java" both exist
            if all(word in resume_lower for word in words):
                matched.add(skill)
            else:
                missing.add(skill)

    return matched, missing


def rank_resumes(job_description, resumes: dict):
    """
    job_description: raw string of JD
    resumes: dict of {filename: raw_text}
    returns: list of (filename, tfidf_score, matched_skills, missing_skills)
    sorted by tfidf_score descending
    """
    # Extract skills ONLY from JD
    jd_skills = extract_skills(job_description)

    # Preprocess text for TF-IDF scoring
    processed_jd = preprocess_text(job_description)
    processed_resumes = {
        name: preprocess_text(text) for name, text in resumes.items()
    }

    # TF-IDF vectorization + cosine similarity for ranking
    all_docs = [processed_jd] + list(processed_resumes.values())
    filenames = list(processed_resumes.keys())

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_docs)

    jd_vector = tfidf_matrix[0]
    resume_vectors = tfidf_matrix[1:]
    scores = cosine_similarity(jd_vector, resume_vectors)[0]

    # Build results — match JD skills against raw resume text
    results = []
    for i, filename in enumerate(filenames):
        matched, missing = get_skill_match(jd_skills, resumes[filename])

        results.append((
            filename,
            scores[i],
            matched,
            missing
        ))

    results.sort(key=lambda x: x[1], reverse=True)
    return results