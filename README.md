# Domain-Specific Search Engine (VTU Information Science)

A full-stack search engine for academic study material (PDF, DOCX, TXT). It builds an inverted index from documents and ranks results with **BM25**, with **TF-IDF** computed alongside as a baseline. Results show a highlighted snippet and the page number of the match, and link to the original document.

Developed for the Dr. AIT Information Science & Engineering curriculum.

**Live demo:** https://domain-specific-search-engine-1.onrender.com
(Free hosting: the first request after inactivity can take about a minute while the server wakes up.)

## Screenshots
![Desktop Home](screenshots/desktop-home.png)

![Search Results](screenshots/search-results.png)

![Mobile View](screenshots/mobile-view.png)

## Features
- **Ranked search:** BM25 ranking, with TF-IDF scores shown for comparison.
- **NLP stemming:** the NLTK Porter stemmer matches root words, so "router", "routers" and "routing" find the same content.
- **Stopword removal:** common words ("how", "what", "the") are dropped from queries so natural-language questions rank well.
- **Contextual snippets:** matched words highlighted, with the page number where the match was found.
- **Open Document:** each result links to the original PDF.
- **Bulk upload:** upload several PDF / DOCX / TXT files at once. Re-uploading a file replaces its old index entries (no double counting).
- **Auto-indexing:** files in `sample_docs/` are indexed automatically at startup when the index is empty.
- **Text cache:** extracted text is stored once at upload time, so searches do not re-parse PDFs (tens of milliseconds per query in local tests).
- **Security:** only `.pdf`, `.docx` and `.txt` uploads are accepted, with a 50 MB size limit; filenames are sanitized with `secure_filename()` (blocks path traversal); snippets are HTML-escaped before highlighting (blocks XSS).
- **Automated tests:** a `pytest` suite covers stemming, snippets, upload security and ranking.
- **Responsive UI:** works on desktop and mobile.

## How it works
1. **Upload / index:** text is extracted per page (PyPDF2 / python-docx) and lowercased. Page markers are stripped, then the text is tokenized and **stemmed**. An inverted index maps each stem to `{document: count}`; document lengths are stored for ranking. Both are saved as JSON in `data/`.
2. **Search:** the query is lowercased, stopwords are removed, and the remaining words are stemmed. For each query stem, BM25 (k1 = 1.5, b = 0.75) and smoothed TF-IDF are computed per document and summed. Results are sorted by BM25.
3. **Snippet:** a window around the first match is taken from the cached text, escaped, then all query words are highlighted (matched by stem). The page number comes from page markers inserted during extraction.

## Tech stack
- **Frontend:** React, Vite
- **Backend:** Python, Flask, Flask-CORS, Gunicorn
- **Libraries:** NLTK (Porter stemmer), PyPDF2, python-docx, PyCryptodome (encrypted PDFs), Werkzeug
- **Testing:** pytest

## API
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/upload` | Upload one or more files (form field `file`) |
| GET | `/api/search?q=...` | Ranked results with snippet, score, and path |
| GET | `/api/files/<filename>` | Open an uploaded document |

## Local setup
1. Clone: `git clone https://github.com/kausthubh00/Domain-Specific-Search-Engine.git`
2. Backend:
```bash
   pip install -r requirements.txt
   python app.py
```
   Runs on port 5000. On first start, every file in `sample_docs/` is indexed automatically.
3. Frontend:
```bash
   cd frontend
   npm install
   npm run dev
```
   By default the frontend uses the live Render backend. To use a local backend, create `frontend/.env.local` containing:
```env
   VITE_API_URL=http://127.0.0.1:5000
```
   then restart `npm run dev`.
4. Open the web page and search. You can also upload more PDFs from the page. The `data/` folder is not stored in the repository.

## Running tests
To run the automated `pytest` suite for security, NLP, and ranking validation:
```bash
pip install -r requirements-dev.txt
python -m pytest test_app.py
```

## Evaluation
Run with `python evaluate.py` while the backend is running. There are **7 indexed documents** (BCS502 modules 1–4, a network-layer unit, a lab manual and a model question paper) and two query sets of 16 queries each. Every result is compared with a **random-order baseline** (the 7 documents shuffled 2,000 times per query).

**Set A: natural-language questions, relevance judged by hand.** For each question such as "How does CSMA/CD handle collisions?", I read the documents and marked those that actually explain the topic.

| Method | Hits@1 | Recall@5 | MRR |
|---|---|---|---|
| BM25 | 100% | 1.000 | 1.000 |
| TF-IDF (smoothed) | 87.5% | 1.000 | 0.938 |
| Random order | 22.5% | 0.715 | 0.462 |

**Set B: short keyword queries, frequency-proxy labels** (a document is relevant if the term appears at least 10 times). This is only a sanity check, because BM25 and TF-IDF also rank by term frequency.

| Method | Hits@1 | Recall@5 | MRR |
|---|---|---|---|
| BM25 | 100% | 1.000 | 1.000 |
| TF-IDF (smoothed) | 100% | 1.000 | 1.000 |
| Random order | 35.8% | 0.714 | 0.574 |

**Effect of stopword removal.** Before removing query stopwords ("how", "what", "the", ...), Set A scored BM25 93.8% and TF-IDF 68.8% Hits@1. After, 100% and 87.5%. TF-IDF suffered most because it divides by document length, so filler words favoured the shortest document.

**Reading the results honestly**
- Both ranking methods are far above random chance, so the pipeline works.
- The stopword list was chosen after seeing which queries failed, so part of the gain is tuned on this test set. The question set is also small (16), and the same person wrote the questions and labels.
- With only 7 documents, Recall@5 is easy to satisfy. Hits@1 and MRR are the more informative columns.

## Limitations
- Small corpus (7 documents) and small query sets (16 each). Set A labels were judged by one person; Set B labels are a frequency proxy.
- The stopword list is short and hand-picked, and it is applied to queries only, not to the index.
- Keyword matching with stemming only: no synonyms, semantic understanding or spell correction.
- Scanned or image-only PDFs have no extractable text and are skipped.
- The index is an in-memory JSON file, suitable for a small collection.
- No user accounts or access control.
- On Render's free tier the server sleeps after about 15 minutes and the disk resets on restart or redeploy. The index is rebuilt from `sample_docs/` at startup, so files uploaded through the site are lost.
- The deployed site indexes only the files in `sample_docs/`; a local run with more documents may give different results.

## Deployment (Render)
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app --timeout 180` (the longer timeout leaves time for the startup indexing of `sample_docs/` on the free tier)
- Set `VITE_API_URL` to the backend URL when building the frontend.
- Documents in `sample_docs/` are indexed automatically after each deploy or restart. Files uploaded through the website are not kept.

## Future work
- Spell correction ("did you mean")
- Filters by subject, module, or document type
- Semantic (embedding-based) search on a hosted model
- Persistent storage for documents and the index
- A larger, independently labelled evaluation set

## Project structure
```text
app.py                Flask API, indexing, ranking, snippets
evaluate.py           Evaluation script (Hits@1, Recall@5, MRR, random baseline)
test_app.py           pytest tests
terms_count.py        Helper that counts terms per document (used to label Set B)
requirements.txt      Backend dependencies
requirements-dev.txt  Test dependencies
sample_docs/          Documents indexed automatically at startup
frontend/             React + Vite web interface
screenshots/          Images used in this README
```