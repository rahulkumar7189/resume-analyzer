# create_small_corpus.py
"""Generate a tiny .spacy corpus for quick testing.
It reads the existing filtered corpus (train_filtered.spacy) and writes the first N docs to train_small.spacy.
"""
import spacy
from spacy.tokens import DocBin
import os

INPUT = os.path.join("data", "processed", "train_filtered.spacy")
OUTPUT = os.path.join("data", "processed", "train_small.spacy")
MAX_DOCS = 50  # adjust as needed for a quick test

nlp = spacy.blank("en")
# Load the full DocBin
full_bin = DocBin().from_disk(INPUT)
# Extract Doc objects (requires the vocab)
full_docs = list(full_bin.get_docs(nlp.vocab))
small_docs = full_docs[:MAX_DOCS]

small_bin = DocBin(docs=small_docs)
small_bin.to_disk(OUTPUT)
print(f"Created small corpus with {len(small_docs)} docs at {OUTPUT}")
