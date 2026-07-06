"""
scorer.py
---------
Computes the ATS match score using three transparent, independent components:

  Component 1 – Skill Coverage Score (0-100)
    Direct match: what % of core JD skills appear in the resume?
    Uses alias expansion and implied-skill reasoning so synonyms don't penalise.

  Component 2 – Semantic Similarity Score (0-100)
    Sentence-Transformers (all-MiniLM-L6-v2) cosine similarity between
    the resume skill set and the JD skill set.  Falls back to TF-IDF.

  Component 3 – Experience Fit Score (0-100)
    Computed from parsed experience months vs. the years required in the JD.
    Capped at 100 to avoid penalising over-qualified candidates.

Final ATS Score = weighted average of the three components with
                 domain-adaptive weights supplied by the caller.

Also produces a keyword_match_detail list so the frontend can show
a per-keyword Found / Missing breakdown.
"""
from __future__ import annotations

import re
import json
import sys
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_EMBEDDING_MODEL = None
_EMBEDDINGS_AVAILABLE = False
_EMBEDDING_LOADED = False

def _get_embedding_model():
    global _EMBEDDING_MODEL, _EMBEDDINGS_AVAILABLE, _EMBEDDING_LOADED
    if not _EMBEDDING_LOADED:
        try:
            from sentence_transformers import SentenceTransformer
            _EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
            _EMBEDDINGS_AVAILABLE = True
            print("[scorer] Sentence-Transformers loaded lazily (semantic scoring enabled).")
        except ImportError:
            _EMBEDDING_MODEL = None
            _EMBEDDINGS_AVAILABLE = False
            print("[scorer] WARNING: sentence-transformers not installed. Falling back to TF-IDF.")
        _EMBEDDING_LOADED = True
    return _EMBEDDING_MODEL, _EMBEDDINGS_AVAILABLE

# ── Helpers ───────────────────────────────────────────────────────────────────

def _tfidf_similarity(text_a: str, text_b: str) -> float:
    """Return 0-1 cosine similarity using TF-IDF (fallback)."""
    if not text_a.strip() or not text_b.strip():
        return 0.0
    vectorizer = TfidfVectorizer(stop_words="english", lowercase=True)
    try:
        matrix = vectorizer.fit_transform([text_a, text_b])
        return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    except ValueError:
        return 0.0


def _semantic_similarity(text_a: str, text_b: str) -> float:
    """Return 0-1 cosine similarity using sentence embeddings (preferred)."""
    model, available = _get_embedding_model()
    if not available:
        return _tfidf_similarity(text_a, text_b)
    from sentence_transformers import util as st_util
    emb_a = model.encode(text_a, convert_to_tensor=True)
    emb_b = model.encode(text_b, convert_to_tensor=True)
    score = float(st_util.cos_sim(emb_a, emb_b)[0][0])
    return max(0.0, min(1.0, score))


def _hybrid_similarity(text_a: str, text_b: str) -> float:
    """
    Combine Dense Embeddings (synonyms) and Sparse Embeddings (TF-IDF/BM25 exact match)
    using Reciprocal Rank Fusion (RRF).
    """
    dense_sim = _semantic_similarity(text_a, text_b)
    sparse_sim = _tfidf_similarity(text_a, text_b)
    
    # Pseudo-rank mapping for RRF: map [0,1] similarity to rank [1, 20]
    rank_dense = 1.0 + (1.0 - dense_sim) * 19.0
    rank_sparse = 1.0 + (1.0 - sparse_sim) * 19.0
    
    rrf_score = (1.0 / (60.0 + rank_dense)) + (1.0 / (60.0 + rank_sparse))
    
    # Normalize back to 0-1 range
    max_rrf = 2.0 / 61.0
    min_rrf = 2.0 / 80.0
    normalized = (rrf_score - min_rrf) / (max_rrf - min_rrf)
    
    return max(0.0, min(1.0, normalized))


def _clean_jd_skill_key(skill: str) -> str:
    """Strip parenthetical suffixes the LLM sometimes appends.
    e.g. 'natural language processing (nlp)' -> 'natural language processing'
    """
    return re.sub(r'\s*\([^)]*\)', '', skill).strip().lower()


# ── JD skill classification via LLM ──────────────────────────────────────────

def _parse_jd_skill_weights(
    job_description: str,
    llm_client,
    user_id: Optional[str] = None,
) -> dict[str, float]:
    """
    Ask the LLM to classify JD skills into Core (weight 3) and Preferred (weight 1).
    Returns {skill_lower: weight}. Falls back to {} on any error.
    """
    if not llm_client or not job_description.strip():
        return {}

    prompt = (
        "You are an expert technical recruiter. "
        "Read this job description and extract all required skills, tools and technologies. "
        "Classify each as 'core' (explicitly required, must-have) or "
        "'preferred' (nice-to-have, bonus). "
        "Respond ONLY with raw JSON (no markdown):\n"
        '{"core": ["Python", "PostgreSQL", ...], "preferred": ["Docker", "Kubernetes", ...]}\n\n'
        f"Job Description:\n{job_description[:3000]}"
    )

    if not user_id:
        import hashlib
        user_id = hashlib.sha256(job_description.encode("utf-8", errors="ignore")).hexdigest()

    try:
        resp = llm_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=300,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
            user=user_id,
        )
        message = resp.choices[0].message
        if hasattr(message, "refusal") and message.refusal:
            raise ValueError(f"Model refused: {message.refusal}")
        data = json.loads(message.content)
        weights: dict[str, float] = {}
        for skill in data.get("core", []):
            weights[str(skill).lower()] = 3.0
        for skill in data.get("preferred", []):
            weights[str(skill).lower()] = 1.0
        return weights
    except Exception as e:
        print(f"[scorer] Skill-weighting LLM call failed: {e}", file=sys.stderr)
        return {}


# ── Experience years extraction from JD ──────────────────────────────────────

_JD_YEARS_RE = re.compile(
    r'(\d+)\+?\s*(?:to\s*\d+\s*)?years?\s+(?:of\s+)?(?:relevant\s+)?experience',
    re.IGNORECASE,
)


def _extract_jd_years_required(job_description: str) -> Optional[float]:
    """Extract the minimum years of experience required from the JD text."""
    matches = _JD_YEARS_RE.findall(job_description)
    if matches:
        return float(matches[0])
    return None


# ── Component 1: Skill coverage score ────────────────────────────────────────

def _build_expanded_resume_set(
    resume_skills: list[str],
) -> set[str]:
    """
    Build a full expanded set of resume skills including:
    - All aliases that point to any resume skill
    - Implied skills (e.g. PyTorch → Deep Learning)
    """
    try:
        from src.skills_db import IMPLIED_SKILLS, SKILL_ALIASES
    except ImportError:
        return {s.lower() for s in resume_skills}

    resume_lower = {s.lower() for s in resume_skills}
    expanded: set[str] = set(resume_lower)

    # Reverse alias map: canonical → [aliases]
    reverse: dict[str, list[str]] = {}
    for alias, canonical in SKILL_ALIASES.items():
        can_lower = canonical.lower()
        reverse.setdefault(can_lower, []).append(alias.lower())

    # Hoist SKILL_ALIASES lookup outside the loop (was incorrectly imported per-iteration)
    _SA = SKILL_ALIASES

    for skill in list(resume_lower):
        # All aliases of each resume skill
        for alias in reverse.get(skill, []):
            expanded.add(alias)
        # Forward alias (e.g. "reactjs" → "React")
        if skill in _SA:
            expanded.add(_SA[skill].lower())
        # Implied skills (e.g. "pytorch" → ["Deep Learning", "Machine Learning"])
        if skill in IMPLIED_SKILLS:
            for implied in IMPLIED_SKILLS[skill]:
                implied_lower = implied.lower()
                expanded.add(implied_lower)
                for alias in reverse.get(implied_lower, []):
                    expanded.add(alias)

    return expanded


def _skill_coverage_score(
    resume_skills: list[str],
    jd_weights: dict[str, float],
) -> float:
    """
    Compute what fraction of JD core skills are covered by the resume.
    Core skills (weight 3) contribute more to the score than preferred (weight 1).
    Returns 0-100.
    """
    if not jd_weights or not resume_skills:
        return 0.0

    expanded = _build_expanded_resume_set(resume_skills)

    total_weight = 0.0
    matched_weight = 0.0

    for skill, weight in jd_weights.items():
        clean = _clean_jd_skill_key(skill)
        total_weight += weight
        if clean in expanded or skill in expanded:
            matched_weight += weight

    if total_weight == 0:
        return 0.0

    return round((matched_weight / total_weight) * 100, 1)


# ── Component 2: Semantic similarity score ────────────────────────────────────

def _extract_jd_responsibilities(jd_text: str) -> str:
    """Heuristic regex to isolate the 'Responsibilities' or 'What you'll do' block from JD."""
    match = re.search(r'(?i)\b(responsibilities|what you\'?l?l do|duties|what we\'?r?e looking for|expectations)\b[\s:]*(.*?)(?=\n\s*\n[A-Z]|\Z)', jd_text, re.DOTALL)
    if match:
        return match.group(2).strip()
    return jd_text # Fallback to whole JD if we can't segment

def _semantic_score(
    resume_skills: list[str],
    jd_weights: dict[str, float],
    job_description: str,
    resume_experience_text: str = "",
) -> float:
    """
    Segmented Hybrid Semantic similarity.
    1. Skills Match: Resume Skills vs JD Core Stack
    2. Experience Match: Resume Experience Block vs JD Responsibilities Block
    Returns 0-100.
    """
    resume_doc = " ".join(resume_skills)

    if jd_weights:
        core_skills = [s for s, w in jd_weights.items() if w >= 3.0]
        pref_skills = [s for s, w in jd_weights.items() if w < 3.0]
        core_text = " ".join(core_skills)
        pref_text = " ".join(pref_skills)

        core_sim = _hybrid_similarity(resume_doc, core_text) if core_text else 0.0
        pref_sim = _hybrid_similarity(resume_doc, pref_text) if pref_text else 0.0

        skills_blended = (core_sim * 3.0 + pref_sim * 1.0) / 4.0
    else:
        skills_blended = _hybrid_similarity(resume_doc, job_description)

    # Experience -> Responsibilities Match
    if resume_experience_text:
        jd_responsibilities = _extract_jd_responsibilities(job_description)
        exp_sim = _hybrid_similarity(resume_experience_text[:3000], jd_responsibilities[:3000]) # Cap lengths for performance
    else:
        exp_sim = skills_blended # fallback

    # Segmented Average
    final_blended = (skills_blended + exp_sim) / 2.0
    
    return round(final_blended * 100, 1)


# ── Component 3: Experience fit score ────────────────────────────────────────

def _experience_fit_score(
    resume_experience_months: int,
    job_description: str,
) -> float:
    """
    Score how well the candidate's experience years match the JD requirement.
    Returns 0-100. Over-qualified candidates are NOT penalised.
    """
    required_years = _extract_jd_years_required(job_description)

    if required_years is None:
        # No years required mentioned — neutral score
        return 70.0

    resume_years = resume_experience_months / 12.0

    if resume_years >= required_years:
        return 100.0
    elif resume_years == 0:
        return 10.0
    else:
        ratio = resume_years / required_years
        return round(min(100.0, ratio * 100), 1)


# ── Keyword match detail ──────────────────────────────────────────────────────

def _keyword_match_detail(
    resume_skills: list[str],
    jd_weights: dict[str, float],
    skills_by_section: dict[str, list[str]] | None = None,
) -> list[dict]:
    """
    Build a per-keyword breakdown showing which JD skills are found/missing.

    Returns list of:
        {
            "keyword": str,
            "type": "core" | "preferred",
            "found": bool,
            "found_in_sections": [str]   # which resume sections mention it
        }
    """
    if not jd_weights:
        return []

    expanded = _build_expanded_resume_set(resume_skills)
    detail: list[dict] = []

    for skill, weight in sorted(jd_weights.items(), key=lambda x: -x[1]):
        clean = _clean_jd_skill_key(skill)
        found = clean in expanded or skill in expanded

        found_in: list[str] = []
        if found and skills_by_section:
            for section_name, section_skills in skills_by_section.items():
                sec_lower = {s.lower() for s in section_skills}
                if clean in sec_lower or skill in sec_lower:
                    found_in.append(section_name)

        detail.append({
            "keyword": skill,
            "type": "core" if weight >= 3.0 else "preferred",
            "found": found,
            "found_in_sections": found_in,
        })

    return detail


# ── Missing skills ────────────────────────────────────────────────────────────

def _find_missing_skills(
    resume_skills: list[str],
    jd_skill_weights: dict[str, float],
    job_description: str,
    max_missing: int = 12,
) -> list[str]:
    """
    Return skills from the JD that are absent from the resume.
    Core skills (higher weight) are listed first.
    Falls back to TF-IDF vocabulary if jd_weights is empty.
    """
    if not resume_skills:
        return []

    expanded = _build_expanded_resume_set(resume_skills)

    if jd_skill_weights:
        missing = [
            skill
            for skill, _ in sorted(jd_skill_weights.items(), key=lambda x: -x[1])
            if _clean_jd_skill_key(skill) not in expanded
            and skill not in expanded
        ]
        return missing[:max_missing]

    # Fallback: TF-IDF vocabulary extraction
    if not job_description.strip():
        return []

    vectorizer = TfidfVectorizer(
        stop_words="english", lowercase=True, ngram_range=(1, 2)
    )
    try:
        resume_doc = " ".join(resume_skills)
        matrix = vectorizer.fit_transform([resume_doc, job_description])
        vocab = vectorizer.get_feature_names_out()
        resume_idxs = set(matrix[0].nonzero()[1])
        jd_idxs = set(matrix[1].nonzero()[1])
        missing_idxs = jd_idxs - resume_idxs
        raw_missing = [vocab[i] for i in missing_idxs]
        missing = [
            t for t in raw_missing
            if _clean_jd_skill_key(t) not in expanded and t not in expanded
        ]
        return missing[:max_missing]
    except ValueError:
        return []


# ── Public API ────────────────────────────────────────────────────────────────

def calculate_ats_match(
    extracted_resume_skills: list[str],
    job_description_text: str,
    llm_client=None,
    user_id: Optional[str] = None,
    resume_experience_months: int = 0,
    skills_by_section: dict[str, list[str]] | None = None,
    domain_weights: dict[str, float] | None = None,
    resume_experience_text: str = "",
) -> tuple[float, list[str], list[dict]]:
    """
    Calculate the ATS match score using three transparent components.

    Args:
        extracted_resume_skills  : Normalised flat list of skills from the resume.
        job_description_text     : Raw job description string.
        llm_client               : Optional Groq/OpenAI client for JD skill parsing.
        user_id                  : Optional stable identifier for rate-limiting.
        resume_experience_months : Total months of experience (from parser.py).
        skills_by_section        : {section_name: [skills]} for keyword detail.
        domain_weights           : Optional {component: weight} overrides.
        resume_experience_text   : Optional raw text of the EXPERIENCE section for semantic matching.

    Returns:
        (ats_score, missing_skills, keyword_match_detail)
        - ats_score             : float 0-100
        - missing_skills        : list[str] (core missing skills first)
        - keyword_match_detail  : list[{keyword, type, found, found_in_sections}]
    """
    if not extracted_resume_skills or not job_description_text.strip():
        return 0.0, [], []

    # ── Step 1: Classify JD skills ───────────────────────────────────────────
    jd_weights = _parse_jd_skill_weights(job_description_text, llm_client, user_id=user_id)

    # ── Step 2: Three scoring components ────────────────────────────────────
    coverage = _skill_coverage_score(extracted_resume_skills, jd_weights)
    semantic = _semantic_score(extracted_resume_skills, jd_weights, job_description_text, resume_experience_text)
    exp_fit  = _experience_fit_score(resume_experience_months, job_description_text)

    print(f"[scorer] Coverage={coverage}  Semantic={semantic}  ExperienceFit={exp_fit}")

    # ── Step 3: Weighted average ─────────────────────────────────────────────
    # Default weights: skill coverage 40%, semantic fit 40%, experience fit 20%
    # These are overridden by domain-adaptive weights from llm_engine.py
    w = domain_weights or {"coverage": 0.40, "semantic": 0.40, "experience": 0.20}
    final_score = round(
        coverage  * w.get("coverage",  0.40) +
        semantic  * w.get("semantic",  0.40) +
        exp_fit   * w.get("experience", 0.20),
        1,
    )
    final_score = max(0.0, min(100.0, final_score))

    # ── Step 4: Missing skills ────────────────────────────────────────────────
    missing_skills = _find_missing_skills(
        extracted_resume_skills, jd_weights, job_description_text
    )

    # ── Step 5: Keyword match detail ─────────────────────────────────────────
    match_detail = _keyword_match_detail(
        extracted_resume_skills, jd_weights, skills_by_section
    )

    return final_score, missing_skills, match_detail
