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
    KeyBERT uses BERT transformer embeddings to find the most
    relevant keywords — proper NLP, not a lookup table.
    Returns a set of skill strings.
    """
    try:
        # Extract top 20 keywords/phrases
        # keyphrase_ngram_range=(1,2) catches both single words
        # and two-word phrases like "machine learning", "REST API"
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=20,
            use_mmr=True,       # MMR reduces redundant keywords
            diversity=0.5       # Balance between relevance and diversity
        )
        # keywords returns list of (keyword, score) tuples
        skills = set(kw.lower().strip() for kw, score in keywords)
        return skills

    except Exception:
        return set()


def rank_resumes(job_description, resumes: dict):
    """
    job_description: raw string of JD
    resumes: dict of {filename: raw_text}
    returns: list of (filename, tfidf_score, matched_skills, missing_skills)
    sorted by tfidf_score descending
    """
    # Extract skills from JD using KeyBERT (transformer-based)
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

    # Build results with skill gap analysis
    results = []
    for i, filename in enumerate(filenames):
        resume_skills = extract_skills(resumes[filename])
        matched_skills = jd_skills & resume_skills
        missing_skills = jd_skills - resume_skills

        results.append((
            filename,
            scores[i],
            matched_skills,
            missing_skills
        ))

    results.sort(key=lambda x: x[1], reverse=True)
    return results