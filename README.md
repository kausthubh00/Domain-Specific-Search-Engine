# Domain-Specific Search Engine

A full-stack, domain-specific search engine built for academic and document retrieval. This project implements a hybrid ranking algorithm combining **BM25** and **TF-IDF** to accurately retrieve and rank information from custom PDF and DOCX datasets.

## Features
* **Hybrid Ranking:** Compares classic TF-IDF with probabilistic BM25 scoring.
* **O(1) Text Caching:** Lightning-fast search retrieval using pre-extracted text caches.
* **Contextual Snippets:** Regex-powered snippet generation with exact-match highlighting.
* **Secure Uploads:** Backend protected against directory traversal and XSS injection.

## Tech Stack
* **Frontend:** React, Vite
* **Backend:** Python, Flask
* **Libraries:** PyPDF2, python-docx, Werkzeug

## Installation & Setup
1. Clone the repository: `git clone https://github.com/kausthubh00/Domain-Specific-Search-Engine.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the backend: `python app.py` (Runs on port 5000)
4. Run the frontend: `cd frontend && npm run dev`