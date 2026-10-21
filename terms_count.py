import glob
import os
import re
import sys

THRESHOLD = 10  # a document is "relevant" if the term appears this many times

# Add or remove queries here
TERMS = [
    "routing", "ip address", "tcp", "topology", "wireless", "server", "client", "subnet",
    "congestion", "sliding window", "handshake", "crc", "csma", "ethernet",
    "ospf", "udp", "flow control", "error detection", "switching", "firewall",
]

# Short names used in evaluate.py
SHORT = {
    "BCS502-module-1-pdf": "M1",
    "BCS502_Module_2_1": "M2",
    "BCS502-module-3-pdf": "M3",
    "BCS502-module-4-pdf": "M4",
    "unit3-Network_Layer": "UNIT3",
    "CN_Lab_Manual_-_SVIT": "LAB",
    "Answering_Model_Paper_Questions": "PAPER",
}

# Read the cached text files (data/<name>.pdf.txt)
docs = {}
for f in glob.glob(os.path.join("data", "*.txt")):
    name = os.path.basename(f)
    name = name[:-8] if name.endswith(".pdf.txt") else name[:-4]
    with open(f, encoding="utf-8", errors="ignore") as fh:
        docs[name] = fh.read().lower()

if not docs:
    sys.exit("No .txt files found in data/. Run this from the project folder.")

print(f"Documents loaded: {len(docs)}\n")
print("=== Counts per term (documents with at least 1 match) ===")

suggested = {}
for term in TERMS:
    counts = {d: len(re.findall(r"\b" + re.escape(term), txt)) for d, txt in docs.items()}
    nonzero = {SHORT.get(d, d): c for d, c in sorted(counts.items(), key=lambda x: -x[1]) if c}
    print(f"{term:18} -> {nonzero}")
    relevant = [SHORT.get(d, d) for d, c in sorted(counts.items(), key=lambda x: -x[1]) if c >= THRESHOLD]
    suggested[term] = relevant

print(f"\n=== Suggested GROUND_TRUTH (threshold >= {THRESHOLD}) ===")
print("Skipped queries are either in every document, in none, or too sparse.\n")
print("GROUND_TRUTH = {")
for term, rel in suggested.items():
    if len(rel) == 0:
        print(f"    # skipped '{term}': no document reaches {THRESHOLD} occurrences")
    elif len(rel) == len(docs):
        print(f"    # skipped '{term}': appears in all documents, tests nothing")
    else:
        print(f'    "{term}": [{", ".join(rel)}],')
print("}")