import spacy
from spacy.tokens import DocBin
import pathlib

# Paths
def main():
    # The script resides in the project root (d:/NLP). Use the parent directory of this file as the base path.
    base_path = pathlib.Path(__file__).parent  # d:/NLP
    input_path = base_path / "data" / "processed" / "train_filtered.spacy"
    output_path = base_path / "data" / "processed" / "train_filtered_noempty.spacy"

    # Load existing DocBin with a vocab
    nlp = spacy.blank("en")
    doc_bin = DocBin().from_disk(str(input_path))
    docs = list(doc_bin.get_docs(nlp.vocab))
    print(f"Loaded {len(docs)} docs")

    # Filter out empty docs (len == 0 tokens)
    filtered_docs = [doc for doc in docs if len(doc) > 0]
    print(f"Filtered down to {len(filtered_docs)} docs (removed {len(docs) - len(filtered_docs)} empty docs)")

    # Save filtered docs
    new_doc_bin = DocBin(docs=filtered_docs)
    new_doc_bin.to_disk(str(output_path))
    print(f"Saved filtered corpus to {output_path}")

if __name__ == "__main__":
    main()
