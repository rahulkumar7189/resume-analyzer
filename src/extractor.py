"""
extractor.py
------------
Hybrid NER skill extractor combining:
  1. Deep Learning NER (custom trained spaCy model)  -- context-aware entity detection
  2. EntityRuler (rule-based from skills_db.py)      -- guaranteed exact-match detection
  3. RapidFuzz normalization (from skills_db.py)     -- alias deduplication & standardization
  4. Section-aware credibility weighting             -- skills from EXPERIENCE > SKILLS list
"""
from __future__ import annotations

import os
import re
import pdfplumber
import spacy
from spacy.language import Language

from src.skills_db import CANONICAL_SKILLS, SKILL_ALIASES

try:
    from rapidfuzz import process, fuzz
    _RAPIDFUZZ_AVAILABLE = True
except ImportError:
    _RAPIDFUZZ_AVAILABLE = False
    print("[extractor] WARNING: rapidfuzz not installed. Alias normalization disabled. "
          "Run: pip install rapidfuzz")

# ── Module-level cache so the model loads only once per process ───────────────
_nlp_cache: Language | None = None

# Pre-build lowercase canonical list for rapidfuzz
_CANONICAL_LOWER = [s.lower() for s in CANONICAL_SKILLS]

# (Removed _SKILL_FALSE_POSITIVES fallback; the new model is trained to reject these naturally)
def _is_valid_skill(raw: str) -> bool:
    """Return True if the extracted entity looks like a real skill."""
    stripped = raw.strip()
    if not stripped or len(stripped) < 2:
        return False
        
    lower = stripped.lower()
    
    # Reject anything with a comma or ' and ' (the model hallucinated a list)
    if "," in lower or " and " in lower or lower.count(" ") > 3:
        # Unless it's an exact match in our canonical list (e.g. "Amazon Web Services")
        if lower not in _CANONICAL_LOWER:
            return False
    

    # If the skill is in our canonical list or aliases, it's always valid
    if lower in _CANONICAL_LOWER or lower in SKILL_ALIASES:
        return True
    
    # For non-canonical skills detected by the neural model, apply strict filters:
    # 1. Reject pure verb-like tokens (ending in 'ing' and longer than 5 chars)
    if lower.endswith('ing') and len(lower) > 5:
        return False
    # 2. Reject generic noun suffixes (-tion, -ment, -ness, -ity, -ance, -ence)
    for suffix in ('tion', 'ment', 'ness', 'ity', 'ance', 'ence', 'sion'):
        if lower.endswith(suffix) and len(lower) > 6:
            return False
    # 3. Reject very short single words that aren't canonical (e.g. "time", "hand")
    if " " not in lower and len(lower) <= 5:
        return False
        
    return True

# Section credibility weights — skills found in higher-weight sections
# are returned first and scored higher downstream.
_SECTION_CREDIBILITY: dict[str, int] = {
    "EXPERIENCE": 3,
    "PROJECTS": 2,
    "CERTIFICATIONS": 2,
    "EDUCATION": 1,
    "SKILLS": 1,
    "SUMMARY": 1,
    "AWARDS": 1,
    "HEADER": 0,
}


# ── Model loading ─────────────────────────────────────────────────────────────

def _load_hybrid_nlp(model_path: str = "./models/model-best") -> Language:
    """
    Load the custom spaCy model and inject an EntityRuler BEFORE the NER
    component so exact-match patterns take priority over the neural model.
    Results are cached for the lifetime of the Python process.
    """
    global _nlp_cache
    if _nlp_cache is not None:
        return _nlp_cache

    resolved_path = model_path
    if not os.path.exists(resolved_path):
        src_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alt1 = os.path.join(src_parent, model_path.lstrip("./"))
        alt2 = os.path.join(src_parent, "models", "model-best")
        if os.path.exists(alt1):
            resolved_path = alt1
        elif os.path.exists(alt2):
            resolved_path = alt2

    if not os.path.exists(resolved_path):
        raise FileNotFoundError(
            f"Trained model not found at {model_path} (resolved: {resolved_path}). "
            "Please complete training first."
        )

    print(f"[extractor] Loading NER model from '{resolved_path}'...")
    nlp = spacy.load(resolved_path)

    if "entity_ruler" not in nlp.pipe_names:
        ruler = nlp.add_pipe("entity_ruler", before="ner", config={"overwrite_ents": True})
        patterns = []
        for skill in CANONICAL_SKILLS:
            patterns.append({"label": "SKILL", "pattern": skill})
            patterns.append({"label": "SKILL", "pattern": skill.lower()})
            patterns.append({"label": "SKILL", "pattern": skill.title()})
        ruler.add_patterns(patterns)
        print(f"[extractor] EntityRuler injected: {len(patterns)} patterns loaded.")

    _nlp_cache = nlp
    return nlp


# ── Skill normalisation ───────────────────────────────────────────────────────

def _normalize_skill(skill: str) -> str:
    """
    Normalise a raw extracted skill string to its canonical form.

    Priority:
        1. Exact alias dict lookup  (O(1))
        2. RapidFuzz fuzzy lookup   (handles typos / spacing)
        3. Return skill as-is
    """
    skill_lower = skill.strip().lower()

    if skill_lower in SKILL_ALIASES:
        return SKILL_ALIASES[skill_lower]

    if _RAPIDFUZZ_AVAILABLE:
        match = process.extractOne(
            skill_lower,
            _CANONICAL_LOWER,
            scorer=fuzz.WRatio,
            score_cutoff=88,
        )
        if match:
            idx = _CANONICAL_LOWER.index(match[0])
            return CANONICAL_SKILLS[idx]

    return skill.strip()


# ── PDF text extraction ───────────────────────────────────────────────────────

def extract_text(pdf_path: str) -> str:
    """
    Extract plain text from a PDF file using PyMuPDF (fitz).
    Uses block extraction and coordinate sorting to prevent two-column layout scrambling.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    full_text = ""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        for page in doc:
            # "blocks" sorts text into structural paragraphs/columns naturally
            blocks = page.get_text("blocks")
            # Sort blocks by horizontal X coordinate first, then vertical Y coordinate
            blocks.sort(key=lambda b: (b[0], b[1]))
            for b in blocks:
                # index 4 of a text block contains the text string
                if len(b) > 4 and isinstance(b[4], str):
                    full_text += b[4] + "\n"
    except Exception as e:
        print(f"[extractor] PyMuPDF failed: {e}")
        
    return full_text


# ── Regex secondary scan ──────────────────────────────────────────────────────

def _regex_scan_skills(text: str, seen: set[str]) -> list[str]:
    """
    Secondary pass: scan text with regex for every canonical skill.
    Catches multi-word phrases that spaCy tokeniser may split or miss.
    Only adds skills not already found by the NER pipeline.
    """
    extra: list[str] = []
    text_lower = text.lower()
    for skill in CANONICAL_SKILLS:
        key = skill.lower()
        if key in seen:
            continue
        # Use a simple word-boundary compatible check via lookbehind/lookahead
        # that handles hyphenated and dotted tech names (e.g. Next.js, C++)
        pattern = re.escape(key)
        if re.search(r'(?<![a-zA-Z0-9.#+])' + pattern + r'(?![a-zA-Z0-9.#+])', text_lower):
            canonical = _normalize_skill(skill)
            ckey = canonical.lower()
            if ckey not in seen:
                extra.append(canonical)
                seen.add(ckey)
    return extra


# ── Section-aware skill extraction ────────────────────────────────────────────

def extract_skills_with_sections(
    sections: dict[str, str],
) -> dict[str, list[str]]:
    """
    Extract skills from each resume section independently.
    Returns a dict mapping section_name -> list of canonical skills found.

    Skills found in higher-credibility sections (EXPERIENCE, PROJECTS)
    are treated as stronger signals downstream.
    """
    nlp = _load_hybrid_nlp()
    result: dict[str, list[str]] = {}

    for section_name, section_text in sections.items():
        if not section_text.strip():
            continue
        skills: list[str] = []
        seen: set[str] = set()

        doc = nlp(section_text[:10000])  # cap per-section to avoid memory issues
        for ent in doc.ents:
            if ent.label_ != "SKILL":
                continue
            raw = ent.text.strip()
            if not raw or not _is_valid_skill(raw):
                continue
            canonical = _normalize_skill(raw)
            key = canonical.lower()
            if key not in seen:
                skills.append(canonical)
                seen.add(key)

        # Regex second pass for this section
        extra = _regex_scan_skills(section_text, seen)
        skills.extend(extra)

        if skills:
            result[section_name] = skills

    return result


def extract_skills_locally(text: str) -> list[str]:
    """
    Extract and normalise technical skills from resume text.

    Uses the Hybrid NER pipeline (EntityRuler + deep learning NER +
    RapidFuzz normalisation) plus a regex phrase-scan second pass.

    Returns a deduplicated, normalised list of canonical skill names,
    sorted so skills from high-credibility sections come first.
    """
    nlp = _load_hybrid_nlp()
    doc = nlp(text)

    skills: list[str] = []
    seen: set[str] = set()

    for ent in doc.ents:
        if ent.label_ != "SKILL":
            continue
        raw = ent.text.strip()
        if not raw or not _is_valid_skill(raw):
            continue
        canonical = _normalize_skill(raw)
        key = canonical.lower()
        if key not in seen:
            skills.append(canonical)
            seen.add(key)

    # Second pass
    extra = _regex_scan_skills(text, seen)
    skills.extend(extra)

    return skills


def extract_skills_section_aware(
    text: str,
    sections: dict[str, str] | None = None,
) -> tuple[list[str], dict[str, list[str]]]:
    """
    Full section-aware skill extraction.

    Returns:
        (flat_skill_list, skills_by_section)
        - flat_skill_list: deduplicated skills sorted by section credibility
        - skills_by_section: {section_name: [skills]}
    """
    # Always run flat extraction as baseline
    flat_skills = extract_skills_locally(text)

    if not sections:
        return flat_skills, {}

    skills_by_section = extract_skills_with_sections(sections)

    # Build credibility-sorted deduplicated list
    seen: set[str] = set()
    sorted_skills: list[str] = []

    # Iterate sections from highest to lowest credibility
    for section_name in sorted(
        _SECTION_CREDIBILITY.keys(),
        key=lambda s: _SECTION_CREDIBILITY.get(s, 0),
        reverse=True,
    ):
        for skill in skills_by_section.get(section_name, []):
            key = skill.lower()
            if key not in seen:
                sorted_skills.append(skill)
                seen.add(key)

    # Append any skills found by flat extraction that weren't in a named section
    for skill in flat_skills:
        key = skill.lower()
        if key not in seen:
            sorted_skills.append(skill)
            seen.add(key)

    return sorted_skills, skills_by_section
