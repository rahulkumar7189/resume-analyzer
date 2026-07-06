# token_stats.py
import spacy
from spacy.tokens import DocBin
import pathlib

# Adjust the path if needed
DOCBIN_PATH = pathlib.Path('data/processed/train_filtered.spacy')

if not DOCBIN_PATH.is_file():
    raise FileNotFoundError(f"DocBin not found at {DOCBIN_PATH}")

# Load a blank nlp for vocab (no model needed)
nlp = spacy.blank('en')

doc_bin = DocBin().from_disk(str(DOCBIN_PATH))

token_counts = [len(doc) for doc in doc_bin.get_docs(nlp.vocab)]

if not token_counts:
    print('No documents found')
else:
    total = len(token_counts)
    avg = sum(token_counts) / total
    mx = max(token_counts)
    mn = min(token_counts)
    print(f'Documents: {total}')
    print(f'Average tokens per doc: {avg:.2f}')
    print(f'Min tokens in a doc: {mn}')
    print(f'Max tokens in a doc: {mx}')
