import sys
import requests

# Default to local, but allow passing the live Render URL via command line
API_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000/api/search"

# Only documents that are actually indexed, and only where the term is discussed
# substantially. PROVISIONAL: verify each list with term_counts.py / Ctrl+F.
M1 = "BCS502-module-1-pdf.pdf"
M2 = "BCS502_Module_2_1.pdf"
M3 = "BCS502-module-3-pdf.pdf"
M4 = "BCS502-module-4-pdf.pdf"
UNIT3 = "unit3-Network_Layer.pdf"
LAB = "CN_Lab_Manual_-_SVIT.pdf"
PAPER = "Answering_Model_Paper_Questions.pdf"

GROUND_TRUTH = {
    "routing": [UNIT3, M3, LAB, M1],
    "ip address": [LAB, UNIT3, M3],
    "tcp": [M4, LAB, PAPER, M1, M3],
    "topology": [LAB, M1],
    "wireless": [M1],
    "server": [PAPER, LAB, M4, M3],
    "client": [PAPER, M4, LAB, M3],
    "subnet": [M3, UNIT3, LAB],
    "congestion": [M4, PAPER, LAB],
    # skipped 'sliding window': no document reaches 10 occurrences
    # skipped 'handshake': no document reaches 10 occurrences
    "crc": [LAB],
    "csma": [M2],
    # skipped 'ethernet': no document reaches 10 occurrences
    "ospf": [M3, UNIT3],
    "udp": [M4, LAB, M1],
    "flow control": [M4],
    "error detection": [M2],
    "switching": [UNIT3, M1],
    # skipped 'firewall': no document reaches 10 occurrences
}


def get_results(query):
    response = requests.get(API_URL, params={"q": query}, timeout=30)
    response.raise_for_status()
    return response.json()


def sort_by(results, algorithm):
    if algorithm == "bm25":
        key = lambda x: float(x["score"].split("BM25: ")[1].split(" |")[0])
    else:
        key = lambda x: float(x["score"].split("TF-IDF: ")[1])
    return sorted(results, key=key, reverse=True)


def evaluate_engine():
    print(f"Testing against: {API_URL}")
    print("-" * 50)

    for algorithm in ["bm25", "tfidf"]:
        total_mrr = 0.0
        total_recall = 0.0
        hits_at_1 = 0
        total_queries = len(GROUND_TRUTH)

        for query, expected_docs in GROUND_TRUTH.items():
            try:
                results = get_results(query)
            except Exception as e:
                print(f"[!] {algorithm} '{query}': request failed ({e})")
                continue  # counts as a failure: total_queries is fixed

            if not results:
                print(f"MISS {algorithm} '{query}': no results")
                continue

            results = sort_by(results, algorithm)
            top_5 = [r["path"] for r in results[:5]]

            # Hits@1: was the very first result relevant?
            if top_5[0] in expected_docs:
                hits_at_1 += 1
            else:
                print(f"MISS {algorithm} '{query}': got {top_5[0]}, expected {expected_docs}")

            # Recall@5: how many relevant docs appear in the top 5?
            found = sum(1 for doc in expected_docs if doc in top_5)
            total_recall += found / len(expected_docs)

            # MRR: reciprocal rank of the first relevant result
            for index, result in enumerate(results):
                if result["path"] in expected_docs:
                    total_mrr += 1.0 / (index + 1)
                    break

        print(f"--- {algorithm.upper()} RESULTS ({total_queries} queries) ---")
        print(f"Hits@1 (Top Result Accuracy): {hits_at_1 / total_queries * 100:.1f}%")
        print(f"Recall@5: {total_recall / total_queries:.4f}")
        print(f"MRR: {total_mrr / total_queries:.4f}\n")


if __name__ == "__main__":
    evaluate_engine()