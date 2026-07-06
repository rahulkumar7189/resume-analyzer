"""
bootstrap_dataset.py
--------------------
Downloads raw PDF resumes from the 'd4rk3r/resumes-raw-pdf' dataset,
extracts text from them, and uses our ALREADY TRAINED model
to automatically predict SKILL entities.

This generates "Silver Data" which we can then merge and train on.
"""
import os
import json
import time
import urllib.request
import tempfile
from pathlib import Path
from PyPDF2 import PdfReader

import spacy
from spacy.tokens import DocBin

DATASET = "d4rk3r/resumes-raw-pdf"
SPLIT = "train"
BATCH = 100
MAX_ROWS = 1940
OUT_SILVER = Path("data/processed/silver_resumes.spacy")
CHECKPOINT = Path("data/processed/silver_checkpoint.spacy")

def build_api_url(offset: int, length: int) -> str:
    import urllib.parse
    params = urllib.parse.urlencode({
        "dataset": DATASET,
        "config": "default",
        "split": SPLIT,
        "offset": offset,
        "length": length,
    })
    return f"https://datasets-server.huggingface.co/rows?{params}"

def fetch_batch(offset: int, length: int, retries: int = 5) -> list[dict]:
    url = build_api_url(offset, length)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data.get("rows", [])
        except Exception as e:
            if attempt < retries - 1:
                wait = 5 * (2 ** attempt)
                print(f"API Retry {attempt+1}... ({e})")
                time.sleep(wait)
            else:
                raise

def extract_text_from_url(pdf_url: str) -> str:
    """Downloads a PDF into memory/tempfile and extracts text."""
    try:
        req = urllib.request.Request(pdf_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            pdf_data = resp.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_data)
            tmp_path = tmp.name
            
        reader = PdfReader(tmp_path)
        texts = []
        for page in reader.pages:
            try:
                extracted = page.extract_text()
                if extracted:
                    texts.append(extracted)
            except Exception:
                pass
                
        os.remove(tmp_path)
        return "\n".join(texts)
    except Exception as e:
        return ""

def main():
    model_dir = Path("./models/model-best")
    if not model_dir.exists():
        print("Error: Base model not found! Train the main model first.")
        return

    print("🧠 Loading base NER model to predict labels...")
    nlp = spacy.load(model_dir)
    blank_nlp = spacy.blank("en") # Used for saving to avoid bloated file size
    
    start_offset = 0
    db = DocBin()
    if CHECKPOINT.exists():
        db = DocBin().from_disk(CHECKPOINT)
        start_offset = len(list(db.get_docs(blank_nlp.vocab)))
        print(f"Resuming from checkpoint: {start_offset} docs")

    total_docs = start_offset
    total_skills = 0
    
    print(f"\n🚀 Starting Bootstrap Labeling of {MAX_ROWS} PDFs...")
    
    api_offset = (start_offset // BATCH) * BATCH
    skip_within_batch = start_offset % BATCH
    
    for offset in range(api_offset, MAX_ROWS, BATCH):
        rows = fetch_batch(offset, BATCH)
        if not rows:
            break
            
        for i, row in enumerate(rows):
            if offset == api_offset and i < skip_within_batch:
                continue
                
            pdf_url = row.get("row", {}).get("pdf", {}).get("src", "")
            if not pdf_url:
                continue
                
            text = extract_text_from_url(pdf_url)
            if not text.strip():
                continue
                
            # Limit text length to avoid memory overload on huge PDFs
            text = text[:10000]
            
            # Predict using our trained model
            doc = nlp(text) 
            
            if len(doc.ents) > 0:
                total_skills += len(doc.ents)
                
                # Save just the text and the entities to a clean doc
                clean_doc = blank_nlp.make_doc(doc.text)
                clean_ents = []
                for ent in doc.ents:
                    span = clean_doc.char_span(ent.start_char, ent.end_char, label=ent.label_)
                    if span:
                        clean_ents.append(span)
                clean_doc.ents = clean_ents
                db.add(clean_doc)
                total_docs += 1
            
            if total_docs % 20 == 0 and total_docs > start_offset:
                print(f"  Processed {total_docs}/{MAX_ROWS} | Found {total_skills} skills")
                CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
                db.to_disk(CHECKPOINT)
                
        time.sleep(1.2) # API rate limit protection
        
    db.to_disk(OUT_SILVER)
    if CHECKPOINT.exists():
        CHECKPOINT.unlink()
        
    print(f"\n✅ Bootstrap complete! Saved {total_docs} auto-annotated resumes to {OUT_SILVER}")

if __name__ == "__main__":
    main()
