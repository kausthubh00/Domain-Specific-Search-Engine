from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import html
import os
import json
import PyPDF2
import docx
import math
import re

app = Flask(__name__)
# Explicitly allow all origins so the frontend never gets blocked
CORS(app, resources={r"/api/*": {"origins": "*"}})

DATA_FOLDER = "data"
INDEX_FILE = os.path.join(DATA_FOLDER, "inverted_index.json")
META_FILE = os.path.join(DATA_FOLDER, "document_meta.json")

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# --- DATABASE LOAD ---
def load_database():
    index = {}
    meta = {}
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r') as f:
            index = json.load(f)
    if os.path.exists(META_FILE):
        with open(META_FILE, 'r') as f:
            meta = json.load(f)
    return index, meta

def save_database():
    with open(INDEX_FILE, 'w') as f:
        json.dump(REAL_INVERTED_INDEX, f)
    with open(META_FILE, 'w') as f:
        json.dump(DOCUMENT_METADATA, f)

REAL_INVERTED_INDEX, DOCUMENT_METADATA = load_database()

# --- HELPER FUNCTIONS ---
def extract_text(file_path, filename):
    text = ""
    try:
        if filename.endswith('.pdf'):
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted: text += extracted.lower() + " "
        elif filename.endswith('.docx'):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text.lower() + " "
        elif filename.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read().lower()
    except Exception as e:
        print(f"[ERROR] Could not read {filename}: {e}")
    return text

def get_highlighted_snippet(text, query):
    """Extracts a 15-word window, secures against XSS, and adds <mark> tags."""
    query_terms = query.lower().split()
    for term in query_terms:
        match = re.search(r'\b' + re.escape(term) + r'\b', text)
        if match:
            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 60)
            
            # Escape the raw text to neutralize malicious scripts
            raw_snippet = "..." + text[start:end] + "..."
            safe_snippet = html.escape(raw_snippet)
            
            # Apply highlights to the sanitized text
            pattern = re.compile(f'({re.escape(term)})', re.IGNORECASE)
            return pattern.sub(r'<mark>\1</mark>', safe_snippet)
            
    return html.escape(text[:120]) + "..." if text else "No preview available."

# --- API ROUTES ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('file')
    if not files:
        return jsonify({"error": "No files found"}), 400
        
    uploaded_names = []
    
    for file in files:
        if file.filename == '': continue
            
        safe_filename = secure_filename(file.filename)
        file_path = os.path.join(DATA_FOLDER, safe_filename)
        file.save(file_path)
        
        text = extract_text(file_path, safe_filename)
        
        cache_path = os.path.join(DATA_FOLDER, safe_filename + ".txt")
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
        words = [w for w in "".join(e if e.isalnum() or e.isspace() else " " for e in text).split() if len(w) > 1]
        
        if not words: continue
            
        DOCUMENT_METADATA[safe_filename] = {
            "title": safe_filename,
            "path": safe_filename, 
            "total_words": len(words)
        }
        
        for word in words:
            if word not in REAL_INVERTED_INDEX:
                REAL_INVERTED_INDEX[word] = {}
            if safe_filename not in REAL_INVERTED_INDEX[word]:
                REAL_INVERTED_INDEX[word][safe_filename] = 0
            REAL_INVERTED_INDEX[word][safe_filename] += 1
            
        uploaded_names.append(safe_filename)
        
    save_database()
    return jsonify({"message": f"Successfully uploaded {len(uploaded_names)} files!"}), 200

@app.route('/api/search', methods=['GET'])
def execute_search():
    query = request.args.get('q', '').lower().strip()
    search_words = [w for w in "".join(e if e.isalnum() or e.isspace() else " " for e in query).split() if len(w) > 1]
    
    if not search_words: return jsonify([])

    document_scores = {}
    total_documents = len(DOCUMENT_METADATA)
    
    avg_doc_length = sum(meta["total_words"] for meta in DOCUMENT_METADATA.values()) / max(1, total_documents)
    k1 = 1.5
    b = 0.75

    for word in search_words:
        if word in REAL_INVERTED_INDEX:
            docs_containing_word = len(REAL_INVERTED_INDEX[word])
            
            idf_tfidf = math.log(total_documents / float(docs_containing_word))
            idf_bm25 = math.log(((total_documents - docs_containing_word + 0.5) / (docs_containing_word + 0.5)) + 1.0)
            
            for filename, term_count in REAL_INVERTED_INDEX[word].items():
                total_words_in_doc = DOCUMENT_METADATA[filename]["total_words"]
                
                tf = term_count / float(total_words_in_doc)
                tfidf_score = tf * idf_tfidf
                
                tf_numerator = term_count * (k1 + 1)
                tf_denominator = term_count + k1 * (1 - b + b * (total_words_in_doc / avg_doc_length))
                bm25_score = idf_bm25 * (tf_numerator / tf_denominator)
                
                if filename not in document_scores:
                    document_scores[filename] = {"tfidf": 0, "bm25": 0}
                    
                document_scores[filename]["tfidf"] += tfidf_score
                document_scores[filename]["bm25"] += bm25_score

    ranked_docs = sorted(document_scores.items(), key=lambda x: x[1]["bm25"], reverse=True)
    
    results = []
    for filename, scores in ranked_docs:
        meta = DOCUMENT_METADATA[filename]
        
        # FIX: Read from the instant text cache instead of re-parsing the heavy PDF
        cache_path = os.path.join(DATA_FOLDER, filename + ".txt")
        raw_text = ""
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
        else:
            file_path = os.path.join(DATA_FOLDER, filename)
            raw_text = extract_text(file_path, filename)
            
        snippet = get_highlighted_snippet(raw_text, query)

        results.append({
            "title": meta["title"],
            "path": meta["path"],
            "snippet": snippet,
            "score": f"BM25: {scores['bm25']:.4f} | TF-IDF: {scores['tfidf']:.4f}",
            "tag": "Ranked Result"
        })

    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Final VTU Engine on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)