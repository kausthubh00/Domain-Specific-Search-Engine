"""
Evaluation for the Domain-Specific Search Engine.

Two query sets are used:
  1. KEYWORD_SET  - short keyword queries. Relevance is a frequency proxy
                    (term appears >= 10 times in the document). Sanity check only,
                    because BM25/TF-IDF also rank by term frequency.
  2. QUESTION_SET - natural-language questions. Relevance was judged BY HAND by
                    reading the documents (a document is relevant if it actually
                    explains the topic). This is the more meaningful test.

Both are compared with a RANDOM baseline (documents in random order, averaged over
many shuffles) so the numbers show how much better than chance the ranking is.

Usage:  python evaluate.py [API_URL]
"""
import random
import sys

import requests

API_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000/api/search"

M1 = "BCS502-module-1-pdf.pdf"
M2 = "BCS502_Module_2_1.pdf"
M3 = "BCS502-module-3-pdf.pdf"
M4 = "BCS502-module-4-pdf.pdf"
UNIT3 = "unit3-Network_Layer.pdf"
LAB = "CN_Lab_Manual_-_SVIT.pdf"
PAPER = "Answering_Model_Paper_Questions.pdf"
ALL_DOCS = [M1, M2, M3, M4, UNIT3, LAB, PAPER]

# 1) Keyword queries, frequency-proxy labels (>= 10 occurrences). Sanity check.
KEYWORD_SET = {
    "routing": [UNIT3, M3, LAB, M1],
    "ip address": [LAB, UNIT3, M3],
    "tcp": [M4, LAB, PAPER, M1, M3],
    "topology": [LAB, M1],
    "wireless": [M1],
    "server": [PAPER, LAB, M4, M3],
    "client": [PAPER, M4, LAB, M3],
    "subnet": [M3, UNIT3, LAB],
    "congestion": [M4, PAPER, LAB],
    "crc": [LAB],
    "csma": [M2],
    "ospf": [M3, UNIT3],
    "udp": [M4, LAB, M1],
    "flow control": [M4],
    "error detection": [M2],
    "switching": [UNIT3, M1],
}

# 2) Natural-language questions, labelled by hand after reading the documents.
QUESTION_SET = {
    "How does TCP congestion control use slow start?": [M4, PAPER],
    "What is Hamming distance and the Hamming code?": [M2],
    "How does CSMA/CD handle collisions?": [M2],
    "What is the Point-to-Point Protocol (PPP)?": [M2],
    "How do BGP and autonomous systems exchange routes?": [M3, UNIT3],
    "How does OSPF use the link-state algorithm?": [UNIT3, M3],
    "What are the features of IPv6?": [M3, UNIT3],
    "How does DHCP automatically assign IP addresses?": [M3, UNIT3],
    "How does the TCP three-way handshake establish a connection?": [M4, PAPER],
    "How does IP fragmentation work?": [M3, UNIT3],
    "How does Manchester line coding represent bits?": [PAPER],
    "How does UDP differ from TCP?": [M4],
    "What is selective repeat ARQ?": [M2],
    "What is flow control in the transport layer?": [M4],
    "What is a socket and how is socket programming done?": [LAB, M4],
    "What is multiplexing and demultiplexing?": [M1, M4],
}


def fetch(query):
    response = requests.get(API_URL, params={"q": query}, timeout=60)
    response.raise_for_status()
    return response.json()


def rank(results, algorithm):
    if algorithm == "bm25":
        key = lambda x: float(x["score"].split("BM25: ")[1].split(" |")[0])
    else:
        key = lambda x: float(x["score"].split("TF-IDF: ")[1])
    return [r["path"] for r in sorted(results, key=key, reverse=True)]


def metrics(ranked, expected):
    """Returns (hit@1, recall@5, reciprocal rank) for one query."""
    hit1 = 1.0 if ranked and ranked[0] in expected else 0.0
    recall5 = len(set(ranked[:5]) & set(expected)) / len(expected)
    rr = 0.0
    for i, path in enumerate(ranked):
        if path in expected:
            rr = 1.0 / (i + 1)
            break
    return hit1, recall5, rr


def random_baseline(truth, shuffles=2000):
    """Expected metrics if the documents were returned in random order."""
    rng = random.Random(42)
    totals = [0.0, 0.0, 0.0]
    for expected in truth.values():
        for _ in range(shuffles):
            order = ALL_DOCS[:]
            rng.shuffle(order)
            for i, value in enumerate(metrics(order, expected)):
                totals[i] += value / shuffles
    n = len(truth)
    return [t / n for t in totals]


def run_engine(truth, algorithm):
    totals = [0.0, 0.0, 0.0]
    for query, expected in truth.items():
        try:
            results = fetch(query)
        except Exception as e:  # a failed request counts as a failed query
            print(f"  [!] {algorithm} '{query}': request failed ({e})")
            continue
        ranked = rank(results, algorithm) if results else []
        values = metrics(ranked, expected)
        if values[0] == 0.0:
            top = ranked[0] if ranked else "no results"
            print(f"  MISS {algorithm} '{query}': got {top}, expected {expected}")
        for i, value in enumerate(values):
            totals[i] += value
    n = len(truth)
    return [t / n for t in totals]


def report(title, truth):
    print(f"\n=== {title} ({len(truth)} queries, {len(ALL_DOCS)} documents) ===")
    rows = [
        ("BM25", run_engine(truth, "bm25")),
        ("TF-IDF", run_engine(truth, "tfidf")),
        ("Random order", random_baseline(truth)),
    ]
    print(f"\n{'Method':<14}{'Hits@1':>9}{'Recall@5':>11}{'MRR':>8}")
    for name, (hit1, recall5, mrr) in rows:
        print(f"{name:<14}{hit1 * 100:>8.1f}%{recall5:>11.3f}{mrr:>8.3f}")


if __name__ == "__main__":
    print(f"Testing against: {API_URL}")
    report("Keyword queries (frequency-proxy labels)", KEYWORD_SET)
    report("Natural-language questions (hand-labelled)", QUESTION_SET)