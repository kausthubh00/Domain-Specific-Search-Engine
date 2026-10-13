import requests
import time

API_URL = "http://127.0.0.1:5000/api/search"

# 20 Test queries for your domain (Networking / Computer Science)
TEST_QUERIES = [
    "network", "tcp", "ip address", "router", "bandwidth",
    "protocol", "osi model", "data link", "packet", "latency",
    "topology", "ethernet", "wireless", "server", "client",
    "firewall", "encryption", "mac address", "socket", "dns"
]

def evaluate_engine():
    print("Starting Search Engine Evaluation...")
    print("-" * 50)
    
    total_mrr = 0
    total_precision = 0
    valid_queries = 0
    
    start_time = time.time()
    
    for query in TEST_QUERIES:
        try:
            response = requests.get(f"{API_URL}?q={query}")
            results = response.json()
            
            if not results:
                continue
                
            valid_queries += 1
            
            # Precision@5: How many of the top 5 results are relevant?
            # (Assuming any returned result containing the exact word is a "hit")
            hits_in_top_5 = sum(1 for r in results[:5] if query in r['snippet'].lower())
            precision_at_5 = hits_in_top_5 / min(5, len(results))
            total_precision += precision_at_5
            
            # MRR (Mean Reciprocal Rank): How high up is the FIRST relevant result?
            mrr_score = 0
            for index, result in enumerate(results):
                if query in result['snippet'].lower():
                    mrr_score = 1.0 / (index + 1)
                    break
            total_mrr += mrr_score
            
        except Exception as e:
            print(f"Error testing query '{query}': {e}")

    execution_time = time.time() - start_time
    
    if valid_queries > 0:
        avg_mrr = total_mrr / valid_queries
        avg_precision = total_precision / valid_queries
        
        print(f"Total Queries Tested: {valid_queries}")
        print(f"Average Search Speed: {(execution_time / valid_queries):.4f} seconds/query")
        print(f"Mean Reciprocal Rank (MRR): {avg_mrr:.4f} (Closer to 1.0 is better)")
        print(f"Precision@5: {avg_precision:.4f} (Closer to 1.0 is better)")
    else:
        print("No results found for any queries. Ensure documents are uploaded first!")

if __name__ == "__main__":
    evaluate_engine()