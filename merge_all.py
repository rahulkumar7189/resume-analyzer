"""
merge_all.py
------------
Merges the three processed corpora into a final training corpus:
1. Gold/Fixed manually annotated data (train_fixed.spacy)
2. HF Seven-Class Skills dataset (seven_class.spacy)
3. Bootstrap auto-labeled resumes from raw PDFs (silver_resumes.spacy)
"""
from pathlib import Path
import spacy
from spacy.tokens import DocBin

# Sourced files
GOLD_PATH = Path("data/processed/train_fixed.spacy")
SEVEN_CLASS_PATH = Path("data/processed/seven_class.spacy")
SILVER_PATH = Path("data/processed/silver_resumes.spacy")

# Destination
FINAL_PATH = Path("data/processed/train_final.spacy")

def merge():
    nlp = spacy.blank("en")
    merged_db = DocBin()
    
    datasets = [
        ("Gold Annotations (train_fixed.spacy)", GOLD_PATH),
        ("HF Seven-Class (seven_class.spacy)", SEVEN_CLASS_PATH),
        ("Silver Auto-Labeled (silver_resumes.spacy)", SILVER_PATH)
    ]
    
    total_docs = 0
    
    print("[*] Merging datasets...")
    for label, path in datasets:
        if path.exists():
            db = DocBin().from_disk(path)
            docs = list(db.get_docs(nlp.vocab))
            print(f"  - Loaded {len(docs):,} docs from {label}")
            for doc in docs:
                merged_db.add(doc)
            total_docs += len(docs)
        else:
            print(f"  - [!] Warning: {label} not found at {path}")
            
    if total_docs > 0:
        FINAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        merged_db.to_disk(FINAL_PATH)
        print(f"\n[+] Successfully merged all corpora!")
        print(f"   Total combined documents: {total_docs:,}")
        print(f"   Saved final training corpus to: {FINAL_PATH}")
        print("\n[+] Ready for training! You can run:")
        print(f"   python -m spacy train config.cfg ^")
        print(f"     --output .\\models ^")
        print(f"     --paths.train .\\{FINAL_PATH} ^")
        print(f"     --paths.dev   .\\data\\processed\\train_fixed.spacy ^")
        print(f"     --gpu-id 0")
    else:
        print("\n[-] Error: No datasets found to merge.")

if __name__ == "__main__":
    merge()
