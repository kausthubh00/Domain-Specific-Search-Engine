import requests
import time

API_URL = "http://127.0.0.1:5000/api/search"

# UPDATE THESE: Map your test queries to the actual PDF filenames they should return
GROUND_TRUTH = {
    "network": ["Answering_Model_Paper_Questions.pdf", "Data_Communications.pdf"],
    "osi model": ["Data_Communications.pdf"],
    "routing": ["Network_Layer.pdf", "Data_Communications.pdf"]
}

def evaluate_engine():
    print("Starting Scientific Search Evaluation (BM25 vs TF-IDF)...")
    print("-" * 60)
    
    for algorithm in ["bm25", "tfidf"]:
        total_mrr = 0
        total_precision = 0
        valid_queries = 0
        start_time = time.time()
        
        for query, expected_docs in GROUND_TRUTH.items():
            try:
                response = requests.get(f"{API_URL}?q={query}")
                results = response.json()
                
                if not results: continue
                valid_queries += 1
                
                # Sort by the current algorithm we are testing
                results.sort(key=lambda x: float(x['score'].split(f"{algorithm.upper()}: ")[1].split(" |")[0] if algorithm == "bm25" else x['score'].split("TF-IDF: ")[1]), reverse=True)
                
                # Precision@5
                top_5_paths = [r['path'] for r in results[:5]]
                hits = sum(1 for doc in expected_docs if doc in top_5_paths)
                total_precision += hits / min(5, len(results))
                
                # MRR
                mrr_score = 0
                for index, result in enumerate(results):
                    if result['path'] in expected_docs:
                        mrr_score = 1.0 / (index + 1)
                        break
                total_mrr += mrr_score
                
            except Exception as e:
                pass
                
        if valid_queries > 0:
            print(f"--- {algorithm.upper()} RESULTS ---")
            print(f"MRR: {total_mrr/valid_queries:.4f} | Precision@5: {total_precision/valid_queries:.4f}")
            print(f"Speed: {(time.time() - start_time)/valid_queries:.4f} sec/query\n")

if __name__ == "__main__":
    evaluate_engine()