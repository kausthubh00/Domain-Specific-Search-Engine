from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import PyPDF2
import time

app = Flask(__name__)
CORS(app) 

REAL_INVERTED_INDEX = {}
DOCUMENT_METADATA = {}
DATA_FOLDER = "data"

def build_real_index():
    print(f"\n--- STARTING LOCAL CRAWLER ---")
    
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
        return

    for filename in os.listdir(DATA_FOLDER):
        if filename.endswith('.pdf'):
            file_path = os.path.join(DATA_FOLDER, filename)
            print(f"Indexing: {filename}...")

            try:
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted.lower() + " "

                    # This will tell us if the PDF is blank or actually has text!
                    print(f"  -> Extracted {len(text)} characters.")

                    DOCUMENT_METADATA[filename] = {
                        "title": filename,
                        "path": os.path.abspath(file_path),
                        "tag": "PDF Document"
                    }

                    words = set(text.split())
                    for word in words:
                        clean_word = "".join(e for e in word if e.isalnum())
                        
                        if len(clean_word) > 1: 
                            if clean_word not in REAL_INVERTED_INDEX:
                                REAL_INVERTED_INDEX[clean_word] = []
                            REAL_INVERTED_INDEX[clean_word].append(filename)
                            
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                
    print(f"--- INDEXING COMPLETE! Total unique words: {len(REAL_INVERTED_INDEX)} ---\n")

@app.route('/api/upload', methods=['POST'])
def upload_file():
    print("\n[BACKEND] File upload request received!")
    
    if 'file' not in request.files:
        return jsonify({"error": "No file found in request"}), 400
        
    file = request.files['file']
    
    if file.filename == '' or not file.filename.endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed!"}), 400
        
    # 1. Save the file
    file_path = os.path.join(DATA_FOLDER, file.filename)
    file.save(file_path)
    print(f"[BACKEND] Successfully saved {file.filename}")
    
    # 2. DYNAMICALLY INDEX THE NEW FILE
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted.lower() + " "
            
            # Add to Metadata
            DOCUMENT_METADATA[file.filename] = {
                "title": file.filename,
                "path": os.path.abspath(file_path),
                "tag": "PDF Document"
            }
            
            # Update the Hash Map in real-time
            words = set(text.split())
            for word in words:
                clean_word = "".join(e for e in word if e.isalnum())
                if len(clean_word) > 1:
                    if clean_word not in REAL_INVERTED_INDEX:
                        REAL_INVERTED_INDEX[clean_word] = []
                    # Prevent duplicates if uploaded twice
                    if file.filename not in REAL_INVERTED_INDEX[clean_word]:
                        REAL_INVERTED_INDEX[clean_word].append(file.filename)
                        
        print(f"[BACKEND] Dynamically indexed '{file.filename}' into memory!")
    except Exception as e:
        print(f"[ERROR] Failed to index new file: {e}")
        return jsonify({"error": "Saved, but failed to index."}), 500
        
    return jsonify({"message": f"Successfully uploaded and indexed {file.filename}!"}), 200
@app.route('/api/search', methods=['GET'])
def execute_search():
    query = request.args.get('q', '').lower().strip()
    print(f"\n[BACKEND] Received query: '{query}'")
    time.sleep(0.5) 

    results = []
    search_words = query.split()
    
    if search_words:
        target_word = "".join(e for e in search_words[0] if e.isalnum())
        print(f"[BACKEND] Searching index for exact word: '{target_word}'")
        
        if target_word in REAL_INVERTED_INDEX:
            matched_files = REAL_INVERTED_INDEX[target_word]
            print(f"[BACKEND] MATCH FOUND! Word is inside {len(matched_files)} files.")
            
            for filename in matched_files:
                meta = DOCUMENT_METADATA[filename]
                results.append({
                    "title": meta["title"],
                    "path": meta["path"],
                    "snippet": f"...document contains the keyword '{target_word}'...",
                    "score": "Ranked Result",
                    "tag": meta["tag"]
                })
        else:
            print(f"[BACKEND] No match. '{target_word}' is not in the index.")

    return jsonify(results)

if __name__ == '__main__':
    build_real_index() 
    print("Starting Phase 1 Flask API Bridge on port 5000...")
    app.run(port=5000, debug=True)