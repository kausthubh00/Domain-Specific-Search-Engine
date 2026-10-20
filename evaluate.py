import requests
import sys

# Default to local, but allow passing the live Render URL via command line
API_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000/api/search"

GROUND_TRUTH = {
    "routing": ["unit3-Network_Layer.pdf", "BCS502-module-3-pdf.pdf", "Data-Communications-and-Network-5e.pdf", "CN_Lab_Manual_-_SVIT.pdf"],
    "osi model": ["BCS502-module-3-pdf.pdf", "Answering_Model_Paper_Questions.pdf", "CN_Lab_Manual_-_SVIT.pdf", "Data-Communications-and-Network-5e.pdf"],
    "ip address": ["unit3-Network_Layer.pdf", "CN_Lab_Manual_-_SVIT.pdf", "Data-Communications-and-Network-5e.pdf"],
    "tcp": ["unit3-Network_Layer.pdf", "BCS502-module-3-pdf.pdf", "BCS502-module-4-pdf.pdf", "Data-Communications-and-Network-5e.pdf", "CN_Lab_Manual_-_SVIT.pdf"],
    "bandwidth": ["BCS502-module-3-pdf.pdf", "Data-Communications-and-Network-5e.pdf"],
    "packet": ["unit3-Network_Layer.pdf", "Data-Communications-and-Network-5e.pdf", "CN_Lab_Manual_-_SVIT.pdf"],
    "topology": ["BCS502-module-3-pdf.pdf", "Data-Communications-and-Network-5e.pdf", "CN_Lab_Manual_-_SVIT.pdf"],
    "wireless": ["BCS502-module-3-pdf.pdf", "Data-Communications-and-Network-5e.pdf"],
    "server": ["Answering_Model_Paper_Questions.pdf", "Data-Communications-and-Network-5e.pdf", "CN_Lab_Manual_-_SVIT.pdf"],
    "client": ["Answering_Model_Paper_Questions.pdf", "Data-Communications-and-Network-5e.pdf", "CN_Lab_Manual_-_SVIT.pdf"],
    "network": ["unit3-Network_Layer.pdf", "BCS502-module-3-pdf.pdf", "Answering_Model_Paper_Questions.pdf", "CN_Lab_Manual_-_SVIT.pdf", "Data-Communications-and-Network-5e.pdf"],
    "protocol": ["unit3-Network_Layer.pdf", "BCS502-module-3-pdf.pdf", "Data-Communications-and-Network-5e.pdf", "BCS502-module-4-pdf.pdf", "CN_Lab_Manual_-_SVIT.pdf"],
    "subnet": ["unit3-Network_Layer.pdf", "Data-Communications-and-Network-5e.pdf", "CN_Lab_Manual_-_SVIT.pdf"],
    "dns": ["Answering_Model_Paper_Questions.pdf", "Data-Communications-and-Network-5e.pdf", "CN_Lab_Manual_-_SVIT.pdf"],
    "latency": ["BCS502-module-3-pdf.pdf", "Data-Communications-and-Network-5e.pdf"]
}
def evaluate_engine():
    print(f"Testing against: {API_URL}")
    print("-" * 50)
    
    for algorithm in ["bm25", "tfidf"]:
        total_mrr = 0
        total_recall = 0
        hits_at_1 = 0
        valid_queries = 0
        
        for query, expected_docs in GROUND_TRUTH.items():
            try:
                response = requests.get(f"{API_URL}?q={query}")
                results = response.json()
                
                if not results: continue
                valid_queries += 1
                
                # Sort by current algorithm
                if algorithm == "bm25":
                    results.sort(key=lambda x: float(x['score'].split("BM25: ")[1].split(" |")[0]), reverse=True)
                else:
                    results.sort(key=lambda x: float(x['score'].split("TF-IDF: ")[1]), reverse=True)
                
                top_5_paths = [r['path'] for r in results[:5]]
                
                # Hits@1: Was the VERY FIRST result relevant?
                if top_5_paths and top_5_paths[0] in expected_docs:
                    hits_at_1 += 1
                
                # Recall@5: Out of all expected files, how many did we find in the top 5?
                found_expected = sum(1 for doc in expected_docs if doc in top_5_paths)
                total_recall += (found_expected / len(expected_docs))
                
                # MRR
                mrr_score = 0
                for index, result in enumerate(results):
                    if result['path'] in expected_docs:
                        mrr_score = 1.0 / (index + 1)
                        break
                total_mrr += mrr_score
                
            except Exception as e:
                print(f"[!] Error on '{query}': {e}")
                
        if valid_queries > 0:
            print(f"--- {algorithm.upper()} RESULTS ---")
            print(f"Hits@1 (Top Result Accuracy): {(hits_at_1/valid_queries)*100:.1f}%")
            print(f"Recall@5: {total_recall/valid_queries:.4f}")
            print(f"MRR: {total_mrr/valid_queries:.4f}\n")

if __name__ == "__main__":
    evaluate_engine()