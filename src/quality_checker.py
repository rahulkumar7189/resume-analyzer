"""
quality_checker.py
------------------
Programmatic resume formatting and structural quality analysis.

Checks (all data-driven, no LLM):
  1. Action verb quality    — % of experience bullets starting with a strong verb
  2. Quantification rate    — % of bullets containing a measurable metric/number
  3. Bullet count and depth — total bullets detected
  4. Resume length estimate — estimated page count (based on word count)
  5. ATS format warnings    — tables, multi-column layout, images, short text
  6. Weak verb detection    — flags "Responsible for...", "Helped with..." etc.
  7. Overall formatting score (0-10)

Usage:
    from src.quality_checker import check_formatting, FormattingScore
    score = check_formatting(resume_text, experience_section_text)
    print(score.overall_formatting_score)
    print(score.ats_format_warnings)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# ── Strong action verb lexicon ────────────────────────────────────────────────

STRONG_ACTION_VERBS: frozenset[str] = frozenset({
    # Technical — Build / Create
    "developed", "engineered", "architected", "designed", "built",
    "implemented", "coded", "programmed", "created", "constructed",
    "established", "founded", "launched", "shipped", "released", "deployed",
    # Technical — Improve / Optimise
    "optimized", "refactored", "improved", "enhanced", "upgraded", "modernized",
    "migrated", "scaled", "automated", "streamlined", "accelerated", "reduced",
    "decreased", "cut", "eliminated", "simplified", "consolidated",
    # Technical — Analyse / Research
    "analyzed", "evaluated", "assessed", "researched", "investigated",
    "benchmarked", "profiled", "modeled", "trained", "fine-tuned",
    "tested", "debugged", "reviewed", "audited", "validated",
    # Technical — Infrastructure / DevOps
    "configured", "provisioned", "containerized", "orchestrated", "monitored",
    "secured", "integrated", "containerised", "virtualized",
    # Data
    "processed", "transformed", "extracted", "aggregated", "visualized",
    "queried", "indexed", "partitioned", "ingested", "pipelined",
    # Leadership / Impact
    "led", "managed", "directed", "headed", "spearheaded", "championed",
    "coordinated", "facilitated", "mentored", "coached", "supervised",
    "collaborated", "partnered", "delivered", "achieved", "exceeded",
    "saved", "generated", "grew", "expanded", "increased", "boosted",
    "doubled", "tripled", "restructured", "standardized",
    # Research / Documentation
    "proposed", "recommended", "presented", "published", "authored",
    "drafted", "documented", "reported", "identified", "resolved",
    "discovered", "pioneered", "invented", "patented",
})

WEAK_VERB_RE = re.compile(
    r'^(?:responsible\s+for|worked\s+on|helped\s+(?:with|to)?|'
    r'assisted\s+(?:with|in)?|involved\s+in|participated\s+in|'
    r'was\s+(?:part\s+of|involved\s+in|responsible\s+for)|'
    r'supported|duties?\s+included|tasks?\s+included|'
    r'contributed\s+to)',
    re.IGNORECASE,
)


# ── Quantification patterns ───────────────────────────────────────────────────

_QUANT_PATTERNS: list[re.Pattern] = [
    re.compile(r'\d+\s*[%％]'),                                     # percentages: 40%, 30%
    re.compile(r'\$\s*\d[\d,]*|\d[\d,]*\s*(?:M|K|B)\b', re.I),    # money: $5M, 200K, 3B
    re.compile(r'\b\d+\+?\s*(?:x|times|fold)\b', re.I),            # multipliers: 3x, 2 times
    re.compile(r'\b(?!(?:19|20)\d{2}\b)\d+\b'),                    # any number that is NOT a 19xx or 20xx year
    re.compile(r'\b(?:one|two|three|four|five|six|seven|eight|nine|ten|dozens?|hundreds?|thousands?)\b', re.I), # spelled out numbers
    re.compile(r'\b(?:from|by|to)\s+\d[\d,.]*'),                   # directional: reduced by 40
]


# ── ATS-unfriendly formatting signals ────────────────────────────────────────

_ATS_CHECKS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(r'(?:\|[^\|]+){2,}\|', re.MULTILINE),
        "Table formatting detected — most ATS parsers cannot parse tables. Convert to plain bullet lists.",
    ),
    (
        re.compile(r'[ \t]{12,}', re.MULTILINE),
        "Excessive whitespace detected — likely multi-column layout. ATS parsers read top-to-bottom; columns cause skills to be missed.",
    ),
    (
        re.compile(r'\.(jpg|jpeg|png|gif|svg|webp|bmp)\b', re.IGNORECASE),
        "Image file reference found — profile photos and chart images are invisible to ATS systems.",
    ),
    (
        re.compile(r'(?:header|footer|text box|text-box)', re.IGNORECASE),
        "Header/footer artifact found — ATS often ignores content inside page headers and footers.",
    ),
    (
        re.compile(r'(?:http|https)://[^\s]{60,}'),
        "Very long URLs detected — consider shortening links with a URL shortener for readability.",
    ),
]

# ── Bullet detection ──────────────────────────────────────────────────────────

_BULLET_LINE_RE = re.compile(r'^[\s]*(?:[•\-–—*>▸▹○◦◆▪●\x88\x0f\uf0b7]|\(cid:\d+\))\s+(.+)', re.MULTILINE)


def _get_bullets(text: str) -> list[str]:
    return [m.group(1).strip() for m in _BULLET_LINE_RE.finditer(text)]


# ── Data class ────────────────────────────────────────────────────────────────

@dataclass
class FormattingScore:
    # Raw counts
    total_bullets: int = 0
    strong_action_verb_count: int = 0
    weak_verb_count: int = 0
    quantified_count: int = 0

    # Derived rates (0.0 – 1.0)
    action_verb_rate: float = 0.0
    quantification_rate: float = 0.0

    # Length
    word_count: int = 0
    estimated_pages: float = 0.0

    # Warnings
    ats_format_warnings: list[str] = field(default_factory=list)

    # Tier 1: Parsability and Completeness
    parsability_score: float = 0.0
    completeness_warnings: list[str] = field(default_factory=list)

    # Aggregate
    overall_formatting_score: float = 0.0   # 0-10

    # Breakdown for the API response
    weak_verb_examples: list[str] = field(default_factory=list)
    strong_verb_examples: list[str] = field(default_factory=list)
    quantified_examples: list[str] = field(default_factory=list)


# ── Main public API ───────────────────────────────────────────────────────────

def check_formatting(
    text: str, 
    experience_section: str = "",
    sections_found: list[str] = None,
    metadata: dict = None
) -> FormattingScore:
    """
    Perform a full programmatic formatting quality check on a resume.

    Args:
        text             : Full raw resume text.
        experience_section: Text of just the EXPERIENCE section (preferred for
                           bullet analysis). Falls back to full text if empty.
        sections_found   : List of section names successfully parsed.
        metadata         : Metadata dict containing email, phone, etc.

    Returns:
        FormattingScore with metrics and an overall_formatting_score (0-10).
    """
    if sections_found is None:
        sections_found = []
    if metadata is None:
        metadata = {}
    score = FormattingScore()

    # Use experience section for bullet analysis if available
    analysis_text = experience_section if experience_section.strip() else text
    bullets = _get_bullets(analysis_text)
    score.total_bullets = len(bullets)

    # ── 1. Action verb and STAR Framework analysis ─────────────────────────────
    # A STAR bullet requires both a strong action verb AND quantification (metrics).
    if bullets:
        quantified = 0
        star_bullets = 0
        for b in bullets:
            tokens = b.split()
            first_word = tokens[0].lower().rstrip('.,;:') if tokens else ""
            
            has_strong_verb = first_word in STRONG_ACTION_VERBS
            has_weak_verb = bool(WEAK_VERB_RE.match(b))
            has_metric = any(p.search(b) for p in _QUANT_PATTERNS)

            if has_strong_verb:
                score.strong_action_verb_count += 1
                score.strong_verb_examples.append(b[:80])
            elif has_weak_verb:
                score.weak_verb_count += 1
                score.weak_verb_examples.append(b[:80])

            if has_metric:
                quantified += 1
                score.quantified_examples.append(b[:80])
                
            if has_strong_verb and has_metric:
                star_bullets += 1

        score.action_verb_rate = round(
            score.strong_action_verb_count / score.total_bullets, 3
        )
        score.quantified_count = quantified
        
        # We redefine quantification_rate to penalize if they aren't STAR formatted
        # i.e., they need both a metric and an action verb
        score.quantification_rate = round(star_bullets / score.total_bullets, 3)

    # ── 3. Resume length ──────────────────────────────────────────────────────
    score.word_count = len(text.split())
    # Average resume page = ~500 words
    score.estimated_pages = round(score.word_count / 500, 1)

    # ── 4. ATS formatting warnings ────────────────────────────────────────────
    for pattern, warning in _ATS_CHECKS:
        if pattern.search(text):
            score.ats_format_warnings.append(warning)

    if score.estimated_pages < 0.3:
        score.ats_format_warnings.append(
            "Resume text is extremely short — the PDF may be image-based or scanned. "
            "ATS parsers cannot read images; use a text-based PDF."
        )
    elif score.estimated_pages > 3.0:
        score.ats_format_warnings.append(
            f"Resume is approximately {score.estimated_pages} pages. "
            "Most recruiters prefer 1 page (junior) or 2 pages (senior). "
            "Consider condensing older experience."
        )

    if score.total_bullets == 0:
        score.ats_format_warnings.append(
            "No bullet points detected in the experience section. "
            "Use bullet-point lists to describe roles — they are significantly "
            "easier to parse and score."
        )

    # ── Tier 1: Completeness & Parsability ────────────────────────────────────
    
    # 1. Parsability
    # For a valid resume, we expect Education, Skills, and either Experience or Projects.
    found_set = set(sections_found)
    has_edu = "EDUCATION" in found_set
    has_skills = "SKILLS" in found_set
    has_exp_or_proj = "EXPERIENCE" in found_set or "PROJECTS" in found_set
    
    score.parsability_score = 100.0
    missing = []
    if not has_edu: missing.append("EDUCATION")
    if not has_skills: missing.append("SKILLS")
    if not has_exp_or_proj: missing.append("EXPERIENCE/PROJECTS")
    
    if missing:
        score.parsability_score = max(0.0, 100.0 - (len(missing) * 25.0))
        score.completeness_warnings.append(
            f"Missing standard sections: {', '.join(missing)}. "
            "Ensure you use standard headings like 'Experience', 'Projects', 'Education', 'Skills'."
        )

    # 2. Completeness
    if not metadata.get("email"):
        score.completeness_warnings.append("No email address found in the contact section.")
    if not metadata.get("phone"):
        score.completeness_warnings.append("No phone number found in the contact section.")

    # ── 5. Compute overall formatting score (0-10) ────────────────────────────
    sub_scores: list[float] = []

    # Action verb score: 80%+ → 10, 60% → 8, 40% → 6, 20% → 4, 0% → 2
    if score.total_bullets > 0:
        av_score = min(10.0, score.action_verb_rate * 12.5)
        sub_scores.append(av_score)
    else:
        sub_scores.append(2.0)  # no bullets is bad

    # Quantification score: 50%+ → 10, 30% → 7, 15% → 5, 0% → 2
    if score.total_bullets > 0:
        q_score = min(10.0, score.quantification_rate * 20.0)
        sub_scores.append(q_score)
    else:
        sub_scores.append(2.0)

    # Length & Density score (Relaxed rules for students/junior candidates)
    # Sweet spot: 250 - 750 words.
    if 250 <= score.word_count <= 750:
        len_score = 10.0
    elif 150 <= score.word_count < 250 or 750 < score.word_count <= 900:
        len_score = 8.0
    elif score.word_count < 150:
        len_score = 5.0  # Too brief
    else:  # > 900 words (too dense)
        len_score = 6.0
    sub_scores.append(len_score)
    
    # Parsability factor (scale the subscore average by parsability)
    base_score = sum(sub_scores) / len(sub_scores)
    base_score = base_score * (0.5 + 0.5 * (score.parsability_score / 100.0))

    # Warning penalty (each formatting warning costs 1.0, completeness warning costs 0.5)
    warning_penalty = min(3.0, len(score.ats_format_warnings) * 1.0 + len(score.completeness_warnings) * 0.5)

    score.overall_formatting_score = round(
        max(0.0, base_score - warning_penalty), 1
    )

    # Trim example lists to keep response payload small
    score.strong_verb_examples = score.strong_verb_examples[:5]
    score.weak_verb_examples = score.weak_verb_examples[:5]
    score.quantified_examples = score.quantified_examples[:5]

    return score
