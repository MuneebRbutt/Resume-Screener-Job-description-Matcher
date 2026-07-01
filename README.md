# 📄 Resume Screener & JD Matcher

An intelligent, NLP-powered resume screening tool that ranks candidates against a job description using semantic similarity, skill gap analysis, and section-aware scoring — the same techniques used by real Applicant Tracking Systems (ATS).

> 🚀 **Live Demo:** https://resume-screener-jd-matcher.streamlit.app/

---

## 📸 Screenshots

<img width="951" height="478" alt="image" src="https://github.com/user-attachments/assets/f833fb69-6f4c-494a-9b67-a127c4b8988b" />

<img width="758" height="455" alt="image" src="https://github.com/user-attachments/assets/2b5af3f8-ef21-45a9-b227-8f191f686caa" />

<img width="729" height="431" alt="image" src="https://github.com/user-attachments/assets/de8eeb68-6269-42d3-9aec-e62c1296074b" />




---

## 🎯 What It Does

Paste a job description, upload multiple resumes (PDF), and the app instantly:

- **Ranks** every resume by how well it matches the JD semantically
- **Shows exactly which skills matched** and which are missing per resume
- **Explains why** each resume scored the way it did (Score Boosters vs Draggers)
- **Breaks down scores** by resume section — Skills, Experience, Education, Projects
- **Visualises** results with an analytics dashboard
- **Exports** ranked results as a CSV or PDF report

---

## ✨ Features

### 1. 🔍 Skill Extraction & Gap Analysis
Extracts the most relevant skills from the job description using **KeyBERT** (transformer-based keyword extraction), then checks each resume for those skills. The result is a clear list of matched skills (green) and missing skills (red) per candidate — not just a black-box percentage.

### 2. 🧠 Semantic Similarity with Sentence Transformers
Uses `sentence-transformers` (`all-MiniLM-L6-v2`) instead of traditional TF-IDF to measure similarity. This means **"ML engineer"** and **"machine learning developer"** correctly score as similar — something TF-IDF completely misses because it only does exact word overlap.

### 3. 📂 Resume Section Parser
Splits each resume into labelled sections — Skills, Experience, Education, Projects, Certifications — and **weights them differently** when computing the final score:

| Section | Weight |
|---|---|
| 🛠 Skills | 45% |
| 💼 Experience | 35% |
| 🚀 Projects | 10% |
| 🎓 Education | 8% |
| 📜 Certifications | 2% |
| Profile / Objective | 0% (noise) |

### 4. 💡 Score Explanation (Explainable AI)
SHAP-inspired keyword attribution — every keyword in the resume is individually encoded and compared to the JD. The top contributors are shown as **Score Boosters** (helped the score) and **Score Draggers** (unrelated noise that pulled it down). This makes the ranking transparent and defensible.

### 5. 📊 Analytics Dashboard
Three interactive charts built with Plotly:
- **Candidate Score Distribution** — bar chart comparing all candidates
- **Most Commonly Missing Skills** — which skills are absent across all resumes
- **Skill Match Rate per Candidate** — stacked bar showing matched vs missing %

### 6. 💾 Export Results
- **CSV** — full ranked table with scores, matched skills, missing skills, section breakdown. Opens directly in Excel.
- **PDF Report** — formatted report per candidate. Ready to share with a hiring manager.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit |
| Semantic Similarity | `sentence-transformers` — `all-MiniLM-L6-v2` |
| Keyword Extraction | KeyBERT |
| NLP / Tokenization | spaCy (`en_core_web_sm`) |
| PDF Parsing | pdfplumber |
| Data Handling | Pandas |
| Visualisation | Plotly |
| PDF Export | fpdf2 |
| Language | Python 3.10+ |

---

## 📁 Project Structure

```
Resume-Screener/
│
├── app.py               # Streamlit UI — all rendering, charts, export buttons
├── nlp_engine.py        # Core NLP — semantic scoring, skill matching, score explanation
├── section_parser.py    # Splits resume text into labelled sections with weights
├── resume_parser.py     # Extracts raw text from uploaded PDF files
│
├── requirements.txt     # All Python dependencies
├── packages.txt         # System-level packages for Streamlit Cloud
└── README.md            # This file
```

---

## ⚙️ How It Works — Pipeline

```
User uploads JD + PDF resumes
        │
        ▼
resume_parser.py
  └── Extracts raw text from each PDF using pdfplumber
        │
        ▼
section_parser.py
  └── Detects section headers (Skills, Experience, Education...)
  └── Splits resume into labelled sections
        │
        ▼
nlp_engine.py
  ├── KeyBERT extracts top 20 skills/keywords from JD
  ├── Sentence Transformer encodes JD into a 384-dim vector
  ├── Each resume section encoded separately → weighted score computed
  ├── Skill gap: JD skills searched directly in resume text
  └── Score explanation: each resume keyword scored against JD vector
        │
        ▼
app.py
  └── Renders ranked results, charts, expanders, export buttons
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Git

### 1. Clone the repository
```bash
git clone https://github.com/MuneebRbutt/Resume-Screener-Job-description-Matcher.git
cd Resume-Screener-Job-description-Matcher
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Download spaCy language model
```bash
python -m spacy download en_core_web_sm
```

### 5. Run the app
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 📦 requirements.txt

```
streamlit
pandas
plotly
spacy
nltk
scikit-learn
sentence-transformers
keybert
fpdf2
pdfplumber
https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
```

---

## ☁️ Deployment — Streamlit Community Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New App**
4. Select your repository, branch (`main`), and main file (`app.py`)
5. Click **Deploy**

First deploy takes 5–10 minutes as it downloads the transformer models. After that you get a permanent public URL like:
```
https://muneeb-resume-screener.streamlit.app
```

---

## 💡 How to Use

1. **Paste a Job Description** into the left panel
2. **Upload PDF resumes** (one or multiple) on the right
3. Click **🔍 Screen Resumes**
4. View:
   - 🏆 Ranked candidates with match scores
   - 📊 Analytics dashboard with charts
   - 👁 Per-resume skill breakdown (click to expand)
   - 🔍 Score explanation — why each resume scored the way it did
5. Export results as **CSV** or **PDF**

---

## 🧪 Sample Test Data

To quickly test the app, use this job description and three sample resumes:

**Job Description:** Machine Learning Engineer role requiring Python, PyTorch, NLP, BERT, FastAPI, Docker, PostgreSQL, AWS.

**Expected ranking:**
| Rank | Candidate | Profile |
|---|---|---|
| 🥇 1st | Ahmed Khan | Senior ML Engineer — strong match |
| 🥈 2nd | Sara Malik | Data Scientist — partial match |
| 🥉 3rd | Bilal Ahmed | Web Developer — weak match |

---

## 🔮 Future Improvements

- [ ] Support for `.docx` resume format
- [ ] GPT-powered candidate summary per resume
- [ ] Batch email report to recruiter
- [ ] Login system with screening history
- [ ] Bias detection — flag gender/age-coded language in JDs

---

## 👨‍💻 Author

**Muneeb Butt**
- GitHub: [@MuneebRbutt](https://github.com/MuneebRbutt)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---


