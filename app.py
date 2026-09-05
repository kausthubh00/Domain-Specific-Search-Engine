from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import PyPDF2
import docx
import math

app = Flask(__name__)
CORS(app) 

DATA_FOLDER = "data"
INDEX_FILE = os.path.join(DATA_FOLDER, "inverted_index.json")
META_FILE = os.path.join(DATA_FOLDER, "document_meta.json")

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# --- DATABASE LOAD ---
def load_database():
    """Loads the saved index from the hard drive when the server starts."""
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
    """Saves the current index to the hard drive permanently."""
    with open(INDEX_FILE, 'w') as f:
        json.dump(REAL_INVERTED_INDEX, f)
    with open(META_FILE, 'w') as f:
        json.dump(DOCUMENT_METADATA, f)

# Load data into RAM on startup
REAL_INVERTED_INDEX, DOCUMENT_METADATA = load_database()

# --- DOCUMENT PARSER ---
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

# --- API ROUTES ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('file')
    if not files:
        return jsonify({"error": "No files found"}), 400
        
    uploaded_names = []
    
    for file in files:
        if file.filename == '': continue
            
        file_path = os.path.join(DATA_FOLDER, file.filename)
        file.save(file_path)
        
        text = extract_text(file_path, file.filename)
        words = [w for w in "".join(e if e.isalnum() or e.isspace() else " " for e in text).split() if len(w) > 1]
        
        if not words: continue
            
        DOCUMENT_METADATA[file.filename] = {
            "title": file.filename,
            "path": os.path.abspath(file_path),
            "total_words": len(words)
        }
        
        for word in words:
            if word not in REAL_INVERTED_INDEX:
                REAL_INVERTED_INDEX[word] = {}
            if file.filename not in REAL_INVERTED_INDEX[word]:
                REAL_INVERTED_INDEX[word][file.filename] = 0
            REAL_INVERTED_INDEX[word][file.filename] += 1
            
        uploaded_names.append(file.filename)
        
    # SAVE PERMANENTLY AFTER UPLOADING
    save_database()
    print(f"[BACKEND] Successfully indexed and saved {len(uploaded_names)} files to disk.")
        
    return jsonify({"message": f"Successfully uploaded {len(uploaded_names)} files!"}), 200

@app.route('/api/search', methods=['GET'])
def execute_search():
    query = request.args.get('q', '').lower().strip()
    search_words = [w for w in "".join(e if e.isalnum() or e.isspace() else " " for e in query).split() if len(w) > 1]
    
    if not search_words: return jsonify([])

    document_scores = {}
    total_documents = len(DOCUMENT_METADATA)

    # TF-IDF RANKING MATH
    for word in search_words:
        if word in REAL_INVERTED_INDEX:
            docs_containing_word = len(REAL_INVERTED_INDEX[word])
            idf = math.log(total_documents / float(docs_containing_word))
            
            for filename, term_count in REAL_INVERTED_INDEX[word].items():
                total_words_in_doc = DOCUMENT_METADATA[filename]["total_words"]
                tf = term_count / float(total_words_in_doc)
                
                if filename not in document_scores:
                    document_scores[filename] = 0
                document_scores[filename] += (tf * idf)

    ranked_docs = sorted(document_scores.items(), key=lambda x: x[1], reverse=True)
    
    results = []
    for filename, score in ranked_docs:
        meta = DOCUMENT_METADATA[filename]
        results.append({
            "title": meta["title"],
            "path": meta["path"],
            "snippet": f"Found strong matches for your query.",
            "score": f"TF-IDF: {score:.4f}",
            "tag": "Ranked Result"
        })

    return jsonify(results)

if __name__ == '__main__':
    print("Starting Final VTU Engine on port 5000...")
    app.run(port=5000, debug=True)