"""
download_kaggle_structured.py
-----------------------------
Downloads the 'suriyaganesh/resume-dataset-structured' Kaggle dataset (54k resumes),
converts it to spaCy NER format, and merges it with the existing train_final.spacy.

Dataset Structure (relational CSVs)
------------------------------------
  people.csv        -- person_id, name, email, phone
  skills.csv        -- skill_id/skill (master skill list)
  person_skills.csv -- person_id, skill_id (junction table)
  experience.csv    -- person_id, job_title, company, description...
  education.csv     -- person_id, degree, institution...
  abilities.csv     -- person_id, ability text

Conversion Strategy
--------------------
For each person we:
  1. Build a rich text document:
        "Skills: <skill1>, <skill2>, ...  Experience: <job_title at company. description...>"
  2. Locate each skill string inside that text using char offsets
  3. Label those spans as SKILL entities
  4. Add the resulting doc to a DocBin

Output
------
  data/processed/kaggle_structured.spacy  -- new dataset alone
  data/processed/train_combined.spacy     -- merged with train_final.spacy
"""
import sys
import csv
import re
from pathlib import Path
from collections import defaultdict

import spacy
from spacy.tokens import DocBin
from spacy.util import filter_spans

# ── Output paths ──────────────────────────────────────────────────────────────
OUT_KAGGLE  = Path("data/processed/kaggle_structured.spacy")
EXISTING    = Path("data/processed/train_final.spacy")
OUT_COMBINED = Path("data/processed/train_combined.spacy")

# How many skills minimum a person must have to be included
MIN_SKILLS = 2


def download_dataset() -> Path:
    """Download the dataset with kagglehub and return its root path."""
    try:
        import kagglehub
    except ImportError:
        print("ERROR: kagglehub not installed. Run: pip install kagglehub")
        sys.exit(1)

    # Check if already cached to avoid re-downloading
    cached = Path(r"C:\Users\Asus\.cache\kagglehub\datasets\suriyaganesh\resume-dataset-structured\versions\2")
    if cached.exists():
        print(f"[*] Dataset already cached at: {cached}")
        return cached

    print("[*] Downloading 'suriyaganesh/resume-dataset-structured' from Kaggle...")
    path = kagglehub.dataset_download("suriyaganesh/resume-dataset-structured")
    print(f"    Dataset saved to: {path}")
    return Path(path)


def read_csv_safe(filepath: Path, expected_cols: list[str]) -> list[dict]:
    """Read a CSV, skip bad rows, return list of dicts."""
    if not filepath.exists():
        print(f"  [!] File not found: {filepath}")
        return []
    rows = []
    with open(filepath, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Make sure expected columns are present (handle naming variants)
            rows.append(row)
    return rows


def detect_column(row: dict, candidates: list[str]) -> str:
    """Return the value of the first matching column name (case-insensitive)."""
    row_lower = {k.lower().strip(): v for k, v in row.items()}
    for candidate in candidates:
        if candidate.lower() in row_lower:
            return row_lower[candidate.lower()].strip()
    return ""


def build_skill_span(doc, skill_text: str) -> object | None:
    """Find the first occurrence of skill_text in doc and return a span."""
    # Case-insensitive search
    pattern = re.escape(skill_text)
    for m in re.finditer(pattern, doc.text, re.IGNORECASE):
        span = doc.char_span(m.start(), m.end(), label="SKILL", alignment_mode="expand")
        if span is not None:
            return span
    return None


def convert_to_spacy(dataset_path: Path) -> DocBin:
    """
    Read the relational CSVs and convert to a spaCy DocBin.
    Returns the DocBin.
    """
    nlp = spacy.blank("en")
    db  = DocBin()

    # --- Try to locate CSV files (dataset may have a nested folder) ---
    csv_root = dataset_path
    # Some kagglehub versions nest files one level deeper
    nested = list(dataset_path.iterdir())
    if len(nested) == 1 and nested[0].is_dir():
        csv_root = nested[0]

    print(f"    CSV root: {csv_root}")
    print(f"    Files found: {[f.name for f in csv_root.iterdir()]}")

    # --- Read tables ---
    # Files are prefixed with numbers: 01_people.csv, 02_abilities.csv, etc.
    # We auto-detect by matching suffix so the script works regardless of prefix.
    def find_csv(suffix: str) -> Path:
        """Find a CSV file by its suffix (e.g. 'people.csv') ignoring numeric prefixes."""
        for f in sorted(csv_root.glob("*.csv")):
            if f.name.lower().endswith(suffix.lower()):
                return f
        return csv_root / suffix  # fallback to exact name (will trigger not-found warning)

    people_rows        = read_csv_safe(find_csv("people.csv"),       ["person_id"])
    skills_rows        = read_csv_safe(find_csv("skills.csv"),       ["skill"])
    person_skills_rows = read_csv_safe(find_csv("person_skills.csv"),["person_id"])
    experience_rows    = read_csv_safe(find_csv("experience.csv"),   ["person_id"])
    education_rows     = read_csv_safe(find_csv("education.csv"),    ["person_id"])
    abilities_rows     = read_csv_safe(find_csv("abilities.csv"),    ["person_id"])

    # --- Build lookup maps ---
    # 05_person_skills.csv has direct 'skill' column (no separate skill_id join needed)
    person_to_skills: dict[str, list[str]] = defaultdict(list)
    for row in person_skills_rows:
        pid        = detect_column(row, ["person_id", "person"])
        skill_name = detect_column(row, ["skill", "skill_name", "skill_id"])
        if pid and skill_name:
            person_to_skills[pid].append(skill_name)

    # person_id -> list of experience strings  (cols: title, firm)
    person_to_exp: dict[str, list[str]] = defaultdict(list)
    for row in experience_rows:
        pid     = detect_column(row, ["person_id", "person"])
        title   = detect_column(row, ["title", "job_title", "position", "role"])
        company = detect_column(row, ["firm", "company", "company_name", "employer"])
        desc    = detect_column(row, ["description", "details", "summary"])
        if pid:
            parts = [x for x in [title, company, desc] if x]
            if parts:
                person_to_exp[pid].append(". ".join(parts))

    # person_id -> list of education strings  (cols: program, institution)
    person_to_edu: dict[str, list[str]] = defaultdict(list)
    for row in education_rows:
        pid    = detect_column(row, ["person_id", "person"])
        degree = detect_column(row, ["program", "degree", "qualification", "field"])
        inst   = detect_column(row, ["institution", "school", "university", "college"])
        if pid:
            parts = [x for x in [degree, inst] if x]
            if parts:
                person_to_edu[pid].append(". ".join(parts))

    # person_id -> list of abilities
    person_to_abilities: dict[str, list[str]] = defaultdict(list)
    for row in abilities_rows:
        pid     = detect_column(row, ["person_id", "person"])
        ability = detect_column(row, ["ability", "name", "description", "text"])
        if pid and ability:
            person_to_abilities[pid].append(ability)

    # --- Convert each person -> spaCy doc ---
    total = 0
    skipped = 0

    all_pids = set(
        [detect_column(r, ["person_id"]) for r in people_rows]
        + list(person_to_skills.keys())
    )

    print(f"\n[*] Converting {len(all_pids):,} people to spaCy docs...")

    for pid in all_pids:
        if not pid:
            continue
        skills   = person_to_skills.get(pid, [])
        exps     = person_to_exp.get(pid, [])
        edus     = person_to_edu.get(pid, [])
        abilities = person_to_abilities.get(pid, [])

        if len(skills) < MIN_SKILLS:
            skipped += 1
            continue

        # Build a coherent text document for this person
        parts = []
        if skills:
            parts.append("Skills: " + ", ".join(skills))
        if exps:
            parts.append("Experience: " + " | ".join(exps[:3]))  # limit to 3 entries
        if edus:
            parts.append("Education: " + " | ".join(edus[:2]))
        if abilities:
            parts.append("Abilities: " + ", ".join(abilities[:10]))

        text = "  ".join(parts)
        if not text.strip():
            continue

        doc = nlp.make_doc(text)

        # Create SKILL spans for each skill found in the text
        spans = []
        for skill in skills:
            span = build_skill_span(doc, skill)
            if span is not None:
                spans.append(span)

        doc.ents = filter_spans(spans)
        db.add(doc)
        total += 1

        if total % 5000 == 0:
            print(f"  {total:,} docs processed...")

    print(f"\n[+] Conversion complete!")
    print(f"    Docs created : {total:,}")
    print(f"    Skipped (< {MIN_SKILLS} skills): {skipped:,}")
    return db


def merge_with_existing(new_db: DocBin) -> DocBin:
    """Merge newly created DocBin with the existing train_final.spacy."""
    nlp = spacy.blank("en")
    merged = DocBin()

    if EXISTING.exists():
        existing_db = DocBin().from_disk(EXISTING)
        existing_docs = list(existing_db.get_docs(nlp.vocab))
        for doc in existing_docs:
            merged.add(doc)
        print(f"    Existing corpus  : {len(existing_docs):,} docs")
    else:
        print(f"    [!] {EXISTING} not found -- creating standalone corpus only.")

    new_docs = list(new_db.get_docs(nlp.vocab))
    for doc in new_docs:
        merged.add(doc)

    all_docs = list(merged.get_docs(nlp.vocab))
    print(f"    New Kaggle docs  : {len(new_docs):,} docs")
    print(f"    Combined total   : {len(all_docs):,} docs")
    return merged


def main():
    # 1. Download dataset
    dataset_path = download_dataset()

    # 2. Convert to spaCy DocBin
    print("\n[*] Converting relational CSVs to spaCy NER format...")
    kaggle_db = convert_to_spacy(dataset_path)

    # 3. Save standalone
    OUT_KAGGLE.parent.mkdir(parents=True, exist_ok=True)
    kaggle_db.to_disk(OUT_KAGGLE)
    print(f"\n[+] Saved Kaggle corpus -> {OUT_KAGGLE}")

    # 4. Merge with train_final.spacy
    print("\n[*] Merging with existing training corpus...")
    combined_db = merge_with_existing(kaggle_db)
    combined_db.to_disk(OUT_COMBINED)
    print(f"[+] Saved combined corpus -> {OUT_COMBINED}")

    print("\n[+] Done! To train on the expanded dataset, run:")
    print("   python -m spacy train config.cfg ^")
    print(f"     --output .\\models ^")
    print(f"     --paths.train .\\{OUT_COMBINED} ^")
    print(f"     --paths.dev   .\\data\\processed\\train_fixed.spacy ^")
    print(f"     --gpu-id 0")


if __name__ == "__main__":
    main()
