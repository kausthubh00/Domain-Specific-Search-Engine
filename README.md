# Domain-Specific Search Engine (Information Science)

A full-stack, domain-specific search engine built for academic document retrieval. This project implements and scientifically compares a hybrid ranking algorithm combining **BM25** and **TF-IDF** to accurately retrieve information from unstructured PDF, DOCX, and TXT datasets. 

Developed for the Dr. AIT Information Science & Engineering curriculum.

## System Architecture & Features
* **Hybrid Algorithmic Ranking:** Compares classic TF-IDF with probabilistic BM25 mathematical smoothing to prevent zero-scoring on concentrated academic datasets.
* **O(1) Caching Layer:** Bypasses heavy PyPDF2 parsing during search execution via pre-extracted lightweight `.txt` caches, achieving ~15ms query speeds.
* **Contextual UI:** Regex-powered snippet generation with multi-term exact-match highlighting, page number extraction, and rigorous XSS escaping.
* **Secure Pipeline:** Backend guarded against directory traversal attacks via `secure_filename()` implementation.

## Evaluation Metrics (BM25 vs TF-IDF)
*(Based on ground-truth academic queries)*
* **BM25:** MRR: 0.3846 | Precision@5: 0.1923 | Speed: ~0.25 sec/query
* **TF-IDF:** MRR: 0.3846 | Precision@5: 0.1923 | Speed: ~0.05 sec/query

## Local Setup
1. `git clone https://github.com/kausthubh00/Domain-Specific-Search-Engine.git`
2. `pip install -r requirements.txt`
3. Run Backend: `python app.py` (Port 5000)
4. Run Frontend: `cd frontend && npm run dev`

## Cloud Deployment (Render)
* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `gunicorn app:app`
