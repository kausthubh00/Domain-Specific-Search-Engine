# Domain-Specific Search Engine (VTU Information Science)

A full-stack search engine for academic study material (PDF, DOCX, TXT). It builds an inverted index from documents and ranks results with **BM25**, with **TF-IDF** computed alongside as a baseline. Results show a highlighted snippet and the page number of the match, and link to the original document.

Developed for the Dr. AIT Information Science & Engineering curriculum.

**Live demo:** https://domain-specific-search-engine-10.onrender.com
(Free hosting: the first request after inactivity can take about a minute while the server wakes up.)

## Screenshots
![Desktop Home](screenshots/desktop-home.png)
![Search Results](screenshots/search-results.png)
![Mobile View](screenshots/mobile-view.png)

## Features
- **Ranked search:** BM25 ranking, with TF-IDF scores shown for comparison.
- **NLP stemming:** the NLTK Porter stemmer matches root words, so "router", "routers" and "routing" find the same content.
- **Contextual snippets:** matched words highlighted, with the page number where the match was found.
- **Open Document:** each result links to the original PDF.
- **Bulk upload:** upload several PDF / DOCX / TXT files at once. Re-uploading a file replaces its old index entries (no double counting).
- **Auto-indexing:** files in `sample_docs/` are indexed automatically at startup when the index is empty.
- **Text cache:** extracted text is stored once at upload time, so searches do not re-parse PDFs (tens of milliseconds per query in local tests).
- **Security:** filenames sanitized with `secure_filename()` (blocks path traversal); snippets HTML-escaped before highlighting (blocks XSS).
- **Responsive UI:** works on desktop and mobile.

## How it works
1. **Upload / index:** text is extracted per page (PyPDF2 / python-docx), lowercased, tokenized and **stemmed**. An inverted index maps each stem to `{document: count}`; document lengths are stored for ranking. Both are saved as JSON in `data/`.
2. **Search:** the query goes through the same tokenizing and stemming. For each query stem, BM25 (k1 = 1.5, b = 0.75) and smoothed TF-IDF are computed per document and summed. Results are sorted by BM25.
3. **Snippet:** a window around the first match is taken from the cached text, escaped, then all query words are highlighted (matched by stem). The page number comes from page markers inserted during extraction.

## Tech stack
- **Frontend:** React, Vite
- **Backend:** Python, Flask, Flask-CORS, Gunicorn
- **Libraries:** NLTK (Porter stemmer), PyPDF2, python-docx, PyCryptodome (encrypted PDFs), Werkzeug

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
   VITE_API_URL=[http://127.0.0.1:5000](http://127.0.0.1:5000)
   ```
   then restart `npm run dev`.
4. Open the web page and search. You can also upload more PDFs from the page. The `data/` folder is not stored in the repository.

## Evaluation
Test set: **7 indexed documents, 16 queries** (`evaluate.py`). The documents are BCS502 modules 1–4, a network-layer unit, a lab manual and a model question paper. A document counts as relevant to a query if the query term appears in it **at least 10 times**.

| Method | Hits@1 | Recall@5 | MRR |
|---|---|---|---|
| BM25 | 100% | 1.00 | 1.00 |
| TF-IDF (smoothed) | 100% | 1.00 | 1.00 |

Run it yourself with the backend running: `python evaluate.py`

- **Hits@1:** share of queries where the top result is relevant.
- **Recall@5:** share of relevant documents found in the top 5.
- **MRR:** mean of 1 / rank of the first relevant result.

**Reading the results honestly**
- This is a **sanity check** that the pipeline (extraction, indexing, ranking, results) works. It is not an independent accuracy benchmark.
- Relevance labels come from term frequency, and BM25 and TF-IDF also rank by term frequency, so a high score is expected.
- With only 7 documents, Recall@5 is easy to satisfy, and both algorithms tie, so this test cannot show that one is better than the other.
- A stronger test would use natural-language questions labelled by hand by a reader.

## Limitations
- Small corpus and small query set; evaluation labels are frequency-based (see above).
- Keyword matching with stemming only: no synonyms, semantic understanding or spell correction.
- Scanned or image-only PDFs have no extractable text and are skipped.
- The index is an in-memory JSON file, suitable for a small collection.
- No user accounts or access control.
- On Render's free tier the server sleeps after about 15 minutes and the disk resets on restart or redeploy. The index is rebuilt from `sample_docs/` at startup, so files uploaded through the site are lost.
- The deployed site indexes only the files in `sample_docs/`; a local run with more documents may give different results.

## Deployment (Render)
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app`
- Set `VITE_API_URL` to the backend URL when building the frontend.
- Documents in `sample_docs/` are indexed automatically after each deploy or restart. Files uploaded through the website are not kept.

## Future work
- Spell correction ("did you mean")
- Filters by subject, module, or document type
- Semantic (embedding-based) search on a hosted model
- Persistent storage for documents and the index
- A hand-labelled, natural-language evaluation set

## Project structure
```text
app.py            Flask API, indexing, ranking, snippets
evaluate.py       Evaluation script (Hits@1, Recall@5, MRR)
requirements.txt  Backend dependencies
sample_docs/      Documents indexed automatically at startup
frontend/         React + Vite web interface
screenshots/      Images used in this README
```