"""
diagnose_errors.py
------------------
Evaluates your best trained neural model against the gold validation dataset,
identifies exact errors (False Positives and False Negatives), and prints a 
top-frequency summary. 

Use this tool to find exactly what the model is missing (False Negatives)
and where humans missed labeling a skill in your gold data (False Positives!).
"""
import os
import spacy
from spacy.tokens import DocBin
from collections import Counter

MODEL_PATH = "./models/model-best"
DEV_PATH   = "./data/processed/train_fixed.spacy"

def main():
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Trained model not found at {MODEL_PATH}.")
        print("Please make sure you have finished training the model first!")
        return

    if not os.path.exists(DEV_PATH):
        print(f"Error: Validation dataset not found at {DEV_PATH}.")
        return

    print("[*] Loading model and validation dataset...")
    nlp = spacy.load(MODEL_PATH)
    dev_bin = DocBin().from_disk(DEV_PATH)
    dev_docs = list(dev_bin.get_docs(nlp.vocab))

    print(f"Loaded {len(dev_docs):,} validation documents.")
    print("[*] Analyzing errors (comparing predictions vs gold standard)...")

    false_positives = Counter()
    false_negatives = Counter()

    total_gold_entities = 0
    total_pred_entities = 0

    for i, dev_doc in enumerate(dev_docs):
        # Predict on the raw text
        pred_doc = nlp(dev_doc.text)

        # Get gold entities (char spans)
        gold_spans = {(ent.start_char, ent.end_char): ent.text.strip() for ent in dev_doc.ents if ent.label_ == "SKILL"}
        pred_spans = {(ent.start_char, ent.end_char): ent.text.strip() for ent in pred_doc.ents if ent.label_ == "SKILL"}

        total_gold_entities += len(gold_spans)
        total_pred_entities += len(pred_spans)

        # False Positives: predicted by model, but not in gold
        for span, text in pred_spans.items():
            if span not in gold_spans:
                false_positives[text.lower()] += 1

        # False Negatives: in gold, but missed by model
        for span, text in gold_spans.items():
            if span not in pred_spans:
                false_negatives[text.lower()] += 1

    # Calculate overall metrics
    precision = (total_pred_entities - len(false_positives)) / max(total_pred_entities, 1)
    recall = (total_gold_entities - len(false_negatives)) / max(total_gold_entities, 1)
    f_score = 2 * (precision * recall) / max(precision + recall, 1e-8)

    print("\n" + "="*50)
    print("METRICS SUMMARY ON GOLD DEV SET")
    print("="*50)
    print(f"  Precision : {precision:.2%}")
    print(f"  Recall    : {recall:.2%}")
    print(f"  F-Score   : {f_score:.2%}")
    print(f"  Total Gold Entities: {total_gold_entities:,}")
    print(f"  Total Pred Entities: {total_pred_entities:,}")
    print("="*50)

    print("\n[+] TOP FALSE POSITIVES (Model predicted, but not labeled in Gold)")
    print("   (These are excellent candidates where the human annotator likely missed the label!)")
    print("-"*75)
    for term, count in false_positives.most_common(20):
        print(f"  - {term:<25} -> {count:>3} occurrences")

    print("\n[-] TOP FALSE NEGATIVES (Labeled in Gold, but missed by Model)")
    print("   (These are exact weak spots where your model needs more training exposure!)")
    print("-"*75)
    for term, count in false_negatives.most_common(20):
        print(f"  - {term:<25} -> {count:>3} occurrences")

if __name__ == "__main__":
    main()
