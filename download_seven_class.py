"""
download_seven_class.py
-----------------------
Downloads the `ganchengguang/resume_seven_class` dataset from Hugging Face
via the Datasets Server API, converts it to spaCy NER format, and merges it
with the existing train_fixed.spacy corpus.

Dataset structure
-----------------
Each row has a single field "text" with the format:
    "CATEGORY<tab>content text"

The seven categories are resume section tags (e.g. Skills, Education, Exp...).
Any row whose category contains "skill" (case-insensitive) is converted into a
spaCy doc where the content span is labelled SKILL.

Output
------
  data/processed/seven_class.spacy   – converted dataset alone
  data/processed/train_merged.spacy  – merged with train_fixed.spacy
"""

import json
import time
import urllib.request
from pathlib import Path

import spacy
from spacy.tokens import DocBin, Span
from spacy.util import filter_spans

# ── Config ────────────────────────────────────────────────────────────────────
DATASET   = "ganchengguang/resume_seven_class"
SPLIT     = "train"
BATCH     = 100          # rows per API request (max allowed)
MAX_ROWS  = 78_670       # total rows in the dataset
DELAY     = 1.2          # seconds between every request (avoids 429)
EXISTING  = Path("data/processed/train_fixed.spacy")
OUT_NEW   = Path("data/processed/seven_class.spacy")
OUT_MERGE = Path("data/processed/train_merged.spacy")
CHECKPOINT= Path("data/processed/seven_class_checkpoint.spacy")  # resume support

# Skills category names we've seen in this dataset.
# We match any category that contains one of these substrings (case-insensitive).
SKILL_KEYWORDS = {"skill", "technical", "technology", "competenc", "proficien"}
# ──────────────────────────────────────────────────────────────────────────────


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


def fetch_batch(offset: int, length: int, retries: int = 6) -> list[dict]:
    """Fetch one page of rows with exponential backoff on rate limits."""
    url = build_api_url(offset, length)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                data = json.loads(resp.read())
                return data.get("rows", [])
        except Exception as e:
            if attempt < retries - 1:
                # Exponential backoff: 5s, 10s, 20s, 40s, 80s
                wait = 5 * (2 ** attempt)
                print(f"  Retry {attempt+1}/{retries} after: {e}. Waiting {wait}s...")
                time.sleep(wait)
            else:
                raise


def is_skill_category(category: str) -> bool:
    cat_lower = category.lower()
    return any(kw in cat_lower for kw in SKILL_KEYWORDS)


def row_to_doc(nlp, text_field: str) -> tuple[object, bool]:
    """
    Parse a row's text field ("CATEGORY\\tcontent") and build a spaCy doc.
    Returns (doc, is_skill_row).
    """
    if "\t" in text_field:
        category, content = text_field.split("\t", 1)
        category = category.strip()
        content  = content.strip()
    else:
        category = ""
        content  = text_field.strip()

    if not content:
        return None, False

    doc = nlp.make_doc(content)

    if is_skill_category(category) and content:
        # Label the entire content span as SKILL
        span = doc.char_span(0, len(content), label="SKILL", alignment_mode="expand")
        if span is not None:
            doc.ents = filter_spans([span])

    return doc, is_skill_category(category)


def download_and_convert(nlp: spacy.Language) -> DocBin:
    """Fetch all rows from the API and convert to a DocBin.
    Saves a checkpoint every 5,000 rows so it can resume if interrupted.
    """
    # Resume from checkpoint if it exists
    start_offset = 0
    db = DocBin()
    if CHECKPOINT.exists():
        db = DocBin().from_disk(CHECKPOINT)
        existing_count = len(list(db.get_docs(nlp.vocab)))
        start_offset = (existing_count // BATCH) * BATCH
        print(f"Resuming from checkpoint: {existing_count:,} docs already downloaded "
              f"(offset {start_offset:,})")

    total_docs   = sum(1 for _ in db.get_docs(nlp.vocab))
    total_skills = 0
    seen_categories: set[str] = set()

    print(f"\nDownloading {DATASET}")
    print(f"  {MAX_ROWS:,} rows total | batch={BATCH} | delay={DELAY}s between requests")
    print(f"  Starting at offset {start_offset:,}\n")

    for offset in range(start_offset, MAX_ROWS, BATCH):
        rows = fetch_batch(offset, BATCH)
        if not rows:
            break

        for row in rows:
            text_field = row.get("row", {}).get("text", "")
            if not text_field:
                continue

            # Collect category names for display
            if "\t" in text_field:
                cat = text_field.split("\t", 1)[0].strip()
                seen_categories.add(cat)

            doc, is_skill = row_to_doc(nlp, text_field)
            if doc is not None:
                db.add(doc)
                total_docs += 1
                if is_skill:
                    total_skills += 1

        # Polite delay between every request to avoid 429
        time.sleep(DELAY)

        # Progress + checkpoint save every 5,000 rows
        if offset % 5000 < BATCH:
            pct = min(offset / MAX_ROWS * 100, 100)
            print(f"  {offset:>6,} / {MAX_ROWS:,} rows  ({pct:.1f}%)  "
                  f"docs={total_docs:,}  skill_docs={total_skills:,}")
            # Save checkpoint so we can resume if interrupted
            CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
            db.to_disk(CHECKPOINT)

    print(f"\nDownload complete:")
    print(f"   Total docs       : {total_docs:,}")
    print(f"   Skill docs       : {total_skills:,}")
    print(f"   Categories found : {sorted(seen_categories)}")

    # Clean up checkpoint file on success
    if CHECKPOINT.exists():
        CHECKPOINT.unlink()

    return db


def merge_with_existing(new_db: DocBin, nlp: spacy.Language) -> DocBin:
    """Merge new DocBin with existing train_fixed.spacy."""
    merged = DocBin()

    if EXISTING.exists():
        existing_db = DocBin().from_disk(EXISTING)
        existing_docs = list(existing_db.get_docs(nlp.vocab))
        for doc in existing_docs:
            merged.add(doc)
        print(f"\nExisting corpus  : {len(existing_docs):,} docs")
    else:
        print(f"\nExisting corpus not found at {EXISTING} -- skipping merge.")

    new_docs = list(new_db.get_docs(nlp.vocab))
    for doc in new_docs:
        merged.add(doc)

    all_docs = list(merged.get_docs(nlp.vocab))
    print(f"New dataset      : {len(new_docs):,} docs")
    print(f"Merged total     : {len(all_docs):,} docs")
    return merged


def main():
    nlp = spacy.blank("en")

    # Step 1 -- Download and convert (resumes from checkpoint if interrupted)
    new_db = download_and_convert(nlp)
    OUT_NEW.parent.mkdir(parents=True, exist_ok=True)
    new_db.to_disk(OUT_NEW)
    print(f"\nSaved new dataset -> {OUT_NEW}")

    # Step 2 -- Merge with existing corpus
    merged_db = merge_with_existing(new_db, nlp)
    merged_db.to_disk(OUT_MERGE)
    print(f"Saved merged corpus -> {OUT_MERGE}")

    print("\nReady to train! Run:")
    print(f"   python -m spacy train config.cfg ^")
    print(f"     --output .\\models ^")
    print(f"     --paths.train .\\{OUT_MERGE} ^")
    print(f"     --paths.dev   .\\{OUT_MERGE} ^")
    print(f"     --gpu-id 0")


if __name__ == "__main__":
    main()

