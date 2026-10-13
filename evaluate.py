import requests
import time

API_URL = "http://127.0.0.1:5000/api/search"

# VTU Information Science domain queries mapped to specific index files
GROUND_TRUTH = {
    "routing": ["unit3-Network_Layer.pdf", "BCS502-module-3-pdf.pdf"],
    "osi model": ["BCS502-module-3-pdf.pdf", "Answering Model Paper Questions.pdf"],
    "ip address": ["unit3-Network_Layer.pdf"],
    "tcp": ["unit3-Network_Layer.pdf", "BCS502-module-3-pdf.pdf"],
    "bandwidth": ["BCS502-module-3-pdf.pdf"],
    "packet": ["unit3-Network_Layer.pdf"],
    "topology": ["BCS502-module-3-pdf.pdf"],
    "wireless": ["BCS502-module-3-pdf.pdf"],
    "server": ["Answering Model Paper Questions.pdf"],
    "client": ["Answering Model Paper Questions.pdf"],
    "network": ["unit3-Network_Layer.pdf", "BCS502-module-3-pdf.pdf", "Answering Model Paper Questions.pdf"],
    "protocol": ["unit3-Network_Layer.pdf", "BCS502-module-3-pdf.pdf"],
    "subnet": ["unit3-Network_Layer.pdf"],
    "dns": ["Answering Model Paper Questions.pdf"],
    "latency": ["BCS502-module-3-pdf.pdf"]
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
                
                if not results: 
                    continue
                valid_queries += 1
                
                # Sort by the current algorithm
                if algorithm == "bm25":
                    results.sort(key=lambda x: float(x['score'].split("BM25: ")[1].split(" |")[0]), reverse=True)
                else:
                    results.sort(key=lambda x: float(x['score'].split("TF-IDF: ")[1]), reverse=True)
                
                # Standard Precision@5 calculation
                top_5_paths = [r['path'] for r in results[:5]]
                hits = sum(1 for doc in expected_docs if doc in top_5_paths)
                # Divide by the actual number of results returned (up to 5)
                total_precision += hits / len(top_5_paths)
                
                # MRR calculation
                mrr_score = 0
                for index, result in enumerate(results):
                    if result['path'] in expected_docs:
                        mrr_score = 1.0 / (index + 1)
                        break
                total_mrr += mrr_score
                
            except Exception as e:
                print(f"[!] Error on query '{query}': {e}")
                
        if valid_queries > 0:
            print(f"--- {algorithm.upper()} RESULTS ---")
            print(f"MRR: {total_mrr/valid_queries:.4f} | Precision@5: {total_precision/valid_queries:.4f}")
            print(f"Speed: {(time.time() - start_time)/valid_queries:.4f} sec/query\n")

if __name__ == "__main__":
    evaluate_engine()