import spacy
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

nltk.download('stopwords', quiet=True)
import sys # Import sys to exit if model not found

nltk.download('stopwords', quiet=True)

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("SpaCy model 'en_core_web_sm' not found. Please download it by running:")
    print("python -m spacy download en_core_web_sm")
    sys.exit(1) # Exit the application if the model is not found

def preprocess_text(text):
    """
    Cleans and lemmatizes text using spaCy
    """
    doc = nlp(text.lower())
    tokens = [
        token.lemma_ for token in doc
        if not token.is_stop and not token.is_punct and token.is_alpha
    ]
    return " ".join(tokens)


def rank_resumes(job_description, resumes: dict):
    """
    job_description: raw string of JD
    resumes: dict of {filename: raw_text}
    returns: list of (filename, score) sorted by score descending
    """
    # Preprocess everything
    processed_jd = preprocess_text(job_description)
    processed_resumes = {
        name: preprocess_text(text) for name, text in resumes.items()
    }

    # Combine JD + all resumes for TF-IDF fitting
    all_docs = [processed_jd] + list(processed_resumes.values())
    filenames = list(processed_resumes.keys())

    # TF-IDF Vectorization
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_docs)

    # Cosine similarity between JD (index 0) and each resume
    jd_vector = tfidf_matrix[0]
    resume_vectors = tfidf_matrix[1:]

    scores = cosine_similarity(jd_vector, resume_vectors)[0]

    # Pair filenames with scores and sort
    results = list(zip(filenames, scores))
    results.sort(key=lambda x: x[1], reverse=True)

    return results