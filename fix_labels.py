"""
fix_labels.py – Normalize broken NER labels in the training corpus.

The training data has 8,472 unique labels of the form 'SKILL: <word>'.
NER requires a small fixed label set. This script collapses all of them
to just 'SKILL', then writes a clean .spacy file ready for training.
"""
import spacy
from spacy.tokens import DocBin, Span
from pathlib import Path

INPUT  = Path("data/processed/train_filtered_noempty.spacy")
OUTPUT = Path("data/processed/train_fixed.spacy")

def normalize_label(label: str) -> str:
    """Map any 'SKILL: ...' label to 'SKILL'."""
    if ":" in label:
        prefix = label.split(":")[0].strip().upper()
        return prefix  # e.g. 'SKILL'
    return label.upper()

def main():
    nlp = spacy.blank("en")
    db_in  = DocBin().from_disk(INPUT)
    db_out = DocBin()

    docs = list(db_in.get_docs(nlp.vocab))
    print(f"Loaded {len(docs)} documents.")

    skipped_ents = 0
    total_ents   = 0

    for doc in docs:
        new_ents = []
        for ent in doc.ents:
            norm_label = normalize_label(ent.label_)
            try:
                new_span = Span(doc, ent.start, ent.end, label=norm_label)
                new_ents.append(new_span)
                total_ents += 1
            except Exception:
                skipped_ents += 1

        doc.ents = new_ents
        db_out.add(doc)

    db_out.to_disk(OUTPUT)

    # Quick sanity check
    db_check = DocBin().from_disk(OUTPUT)
    check_docs = list(db_check.get_docs(nlp.vocab))
    from collections import Counter
    labels = Counter(ent.label_ for d in check_docs for ent in d.ents)
    print(f"\n=== Fixed corpus written to: {OUTPUT} ===")
    print(f"Total documents : {len(check_docs)}")
    print(f"Total entities  : {sum(labels.values())}")
    print(f"Unique labels   : {len(labels)}")
    print(f"Label counts    : {dict(labels.most_common(10))}")
    print(f"Skipped entities: {skipped_ents}")

if __name__ == "__main__":
    main()
