"""
clean_dataset_labels.py
-----------------------
Purges common non-skill generic English words (discovered by our diagnostic tool)
from both training and dev datasets. This "Data-Centric AI" clean-up prevents the
model from being penalized or confused by noisy silver annotations.
"""
import os
import spacy
from spacy.tokens import DocBin
from spacy.util import filter_spans

# Paths to original datasets
TRAIN_PATH = "./data/processed/train_expanded.spacy"
DEV_PATH   = "./data/processed/train_fixed.spacy"

# Paths to output clean datasets
TRAIN_CLEAN_PATH = "./data/processed/train_expanded_clean.spacy"
DEV_CLEAN_PATH   = "./data/processed/train_fixed_clean.spacy"

# Generic corporate, academic, and grammatical terms that are NOT skills
BLACKLIST = {
    # Non-skill generic nouns & words
    "company", "system", "work", "project", "is", "skills", "team", "personal", 
    "client", "knowledge", "ltd", "ltd.", "college", "training", "information", 
    "power", "design", "sales", "safety", "board", "quality", "engineer", 
    "engineering", "management", "state", "organization", "electrical", 
    "professional", "data", "department", "university", "school", "business", 
    "services", "experience", "development", "role", "position", "career",
    "summary", "profile", "objective", "responsibilities", "duties",
    # Specific false positives from previous analysis
    "extraction", "time", "hand", "classification", "consumer hardware", 
    "inspection", "normalisation", "curriculum", "detection", "coursework", 
    "linear", "math", "probability", "algorithms", "software", "tools",
    # Stop words / grammatical terms
    "and", "the", "of", "to", "in", "a", "for", "with", "as", "on", "at", "by", "an"
}

def clean_corpus(input_path, output_path, nlp_blank):
    if not os.path.exists(input_path):
        print(f"  [!] Skipping: {input_path} not found.")
        return

    print(f"  [*] Cleaning: {input_path} ...")
    db = DocBin().from_disk(input_path)
    docs = list(db.get_docs(nlp_blank.vocab))
    
    cleaned_docs = []
    removed_count = 0
    total_ents_before = 0
    total_ents_after = 0

    for doc in docs:
        total_ents_before += len(doc.ents)
        
        # Filter spans to exclude any matching our blacklist
        cleaned_spans = []
        for ent in doc.ents:
            text_cleaned = ent.text.strip().lower()
            if text_cleaned in BLACKLIST:
                removed_count += 1
                continue
            cleaned_spans.append(ent)
            
        doc.ents = filter_spans(cleaned_spans)
        cleaned_docs.append(doc)
        total_ents_after += len(doc.ents)

    new_db = DocBin(docs=cleaned_docs)
    new_db.to_disk(output_path)
    print(f"  [+] Saved cleaned dataset to: {output_path}")
    print(f"      Before: {total_ents_before:,} entities | After: {total_ents_after:,} entities")
    print(f"      Removed {removed_count:,} generic entities.")

def main():
    nlp_blank = spacy.blank("en")
    print("[*] Starting Data-Centric Dataset Purge...")
    
    # Clean train dataset
    clean_corpus(TRAIN_PATH, TRAIN_CLEAN_PATH, nlp_blank)
    
    # Clean dev dataset
    clean_corpus(DEV_PATH, DEV_CLEAN_PATH, nlp_blank)
    
    print("\n[+] Data-Centric Purge Complete!")
    print("    Now you have two immaculately clean datasets:")
    print(f"    - Train: {TRAIN_CLEAN_PATH}")
    print(f"    - Dev  : {DEV_CLEAN_PATH}")

if __name__ == "__main__":
    main()
