"""
llm_engine.py
-------------
Groq LLM client for structured resume evaluation.

Improvements over the original:
  1. Domain detection ΓÇö auto-detects job domain (data_science, devops, frontend, etc.)
     and applies domain-adaptive dimension weights so scoring is role-appropriate.
  2. Structured context injection ΓÇö passes parsed resume metadata (experience years,
     highest degree, certifications, formatting score) alongside the raw text so the
     LLM has ground truth to evaluate against instead of guessing.
  3. STAR-format bullet detection ΓÇö LLM is explicitly asked to flag bullets missing
     a quantified outcome.
  4. API key from environment ΓÇö no hardcoded secrets.
"""
from __future__ import annotations

import os
import json
import sys
import re
from typing import Optional
from openai import OpenAI
from pydantic import BaseModel, ValidationError

# ΓöÇΓöÇ Groq client ΓÇö key from environment ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
_GROQ_API_KEY = (
    os.getenv("GROQ_API_KEY")
    or os.getenv("NEXT_PUBLIC_GROQ_API_KEY")
    or "your_api_key_here"  # fallback for local dev
)

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=_GROQ_API_KEY,
)


# ΓöÇΓöÇ Data models ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

from pydantic import BaseModel, Field

class ResumeTip(BaseModel):
    category: str = Field(..., description="Category of the tip: skills_match, experience, education, projects, presentation")
    issue_found: str = Field(..., description="Specific, concrete issue citing the actual resume text.")
    actionable_fix: str = Field(..., description="Step-by-step fix with examples using the STAR format.")
    impact: str = Field(default="medium", description="high, medium, or low")
    star_missing: bool = Field(default=False, description="True if bullet point lacks quantified outcome")


class DimensionScores(BaseModel):
    skills_match: float = Field(..., description="Match between resume skills and JD requirements (0-10)")
    experience: float = Field(..., description="Depth, relevance, and years of work experience (0-10)")
    education: float = Field(..., description="Degree relevance and institution prestige (0-10)")
    projects: float = Field(..., description="Quality, complexity and relevance of projects (0-10)")
    presentation: float = Field(..., description="Clarity, formatting, quantified achievements (0-10)")


class ResumeFeedback(BaseModel):
    llm_ats_fit_score: float = Field(..., description="Holistic ATS fit score evaluating the candidate's true potential and alignment (0-100)")
    dimension_scores: DimensionScores = Field(...)
    improvement_tips: list[ResumeTip] = Field(..., description="Actionable tips for the candidate")
    hr_red_flags: list[str] = Field(default_factory=list, description="Critical HR red flags like bias, vagueness, cliches")
    
    # Internal fields calculated post-parsing
    overall_score: float = 0.0
    domain: str = "software_engineering"


# ΓöÇΓöÇ Fallback ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def _default_feedback(domain: str = "software_engineering") -> ResumeFeedback:
    return ResumeFeedback(
        overall_score=0.0,
        llm_ats_fit_score=0.0,
        domain=domain,
        dimension_scores=DimensionScores(
            skills_match=0.0,
            experience=0.0,
            education=0.0,
            projects=0.0,
            presentation=0.0
        ),
        improvement_tips=[
            ResumeTip(
                category="presentation",
                issue_found="LLM response could not be parsed.",
                actionable_fix="Retry the request or check the Groq API key.",
                impact="high",
                star_missing=False
            )
        ],
        hr_red_flags=["Analysis failed. Default fallback applied."]
    )


# ΓöÇΓöÇ Domain detection ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "data_science": [
        "machine learning", "data science", "ml engineer", "deep learning",
        "nlp", "computer vision", "data scientist", "research scientist",
        "ai engineer", "llm", "large language model",
    ],
    "data_engineering": [
        "data engineer", "data pipeline", "etl", "elt", "spark", "airflow",
        "databricks", "dbt", "snowflake", "data warehouse", "data lake",
        "kafka", "flink", "streaming",
    ],
    "devops": [
        "devops", "sre", "infrastructure", "kubernetes", "terraform",
        "ci/cd", "platform engineer", "cloud engineer", "reliability",
        "ansible", "puppet", "chef", "helm",
    ],
    "security": [
        "security", "penetration testing", "cybersecurity", "soc analyst",
        "siem", "threat", "vulnerability", "ethical hacking", "infosec",
    ],
    "mobile": [
        "android", "ios", "mobile", "react native", "flutter",
        "swift", "kotlin", "jetpack", "swiftui",
    ],
    "frontend": [
        "frontend", "front-end", "ui engineer", "ui/ux", "react developer",
        "vue developer", "angular developer", "css", "web developer",
    ],
    "backend": [
        "backend", "back-end", "api engineer", "server-side", "rest api",
        "microservices", "grpc", "django", "fastapi", "spring boot",
    ],
    "fullstack": [
        "full stack", "fullstack", "full-stack", "end-to-end",
    ],
    "product": [
        "product manager", "product owner", "product analyst", "roadmap",
        "user research", "a/b testing", "growth",
    ],
}


def detect_job_domain(job_description: str) -> str:
    """
    Detect the primary job domain from the JD text.
    Returns one of: data_science, data_engineering, devops, security,
                    mobile, frontend, backend, fullstack, product,
                    software_engineering (default).
    """
    jd_lower = job_description.lower()
    scores: dict[str, int] = {domain: 0 for domain in _DOMAIN_KEYWORDS}

    for domain, keywords in _DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in jd_lower:
                scores[domain] += 1

    best = max(scores, key=lambda d: scores[d])
    return best if scores[best] > 0 else "software_engineering"


# ΓöÇΓöÇ Domain-adaptive dimension weights ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# Weights must sum to 1.0.  Applied to the 5 LLM dimension scores.

_DOMAIN_DIMENSION_WEIGHTS: dict[str, dict[str, float]] = {
    "data_science": {
        "skills_match": 0.30, "experience": 0.20, "education": 0.20,
        "projects": 0.25, "presentation": 0.05,
    },
    "data_engineering": {
        "skills_match": 0.35, "experience": 0.30, "education": 0.10,
        "projects": 0.20, "presentation": 0.05,
    },
    "devops": {
        "skills_match": 0.40, "experience": 0.30, "education": 0.05,
        "projects": 0.20, "presentation": 0.05,
    },
    "security": {
        "skills_match": 0.35, "experience": 0.30, "education": 0.15,
        "projects": 0.15, "presentation": 0.05,
    },
    "mobile": {
        "skills_match": 0.30, "experience": 0.25, "education": 0.10,
        "projects": 0.30, "presentation": 0.05,
    },
    "frontend": {
        "skills_match": 0.25, "experience": 0.20, "education": 0.10,
        "projects": 0.40, "presentation": 0.05,
    },
    "backend": {
        "skills_match": 0.30, "experience": 0.30, "education": 0.10,
        "projects": 0.25, "presentation": 0.05,
    },
    "fullstack": {
        "skills_match": 0.28, "experience": 0.25, "education": 0.08,
        "projects": 0.35, "presentation": 0.04,
    },
    "product": {
        "skills_match": 0.20, "experience": 0.35, "education": 0.15,
        "projects": 0.20, "presentation": 0.10,
    },
    "software_engineering": {
        "skills_match": 0.30, "experience": 0.25, "education": 0.15,
        "projects": 0.20, "presentation": 0.10,
    },
}

# Scorer component weights ΓÇö returned so caller can pass to scorer.py
_DOMAIN_SCORER_WEIGHTS: dict[str, dict[str, float]] = {
    "data_science":      {"coverage": 0.35, "semantic": 0.40, "experience": 0.25},
    "data_engineering":  {"coverage": 0.40, "semantic": 0.35, "experience": 0.25},
    "devops":            {"coverage": 0.45, "semantic": 0.30, "experience": 0.25},
    "security":          {"coverage": 0.40, "semantic": 0.30, "experience": 0.30},
    "mobile":            {"coverage": 0.35, "semantic": 0.40, "experience": 0.25},
    "frontend":          {"coverage": 0.30, "semantic": 0.45, "experience": 0.25},
    "backend":           {"coverage": 0.35, "semantic": 0.40, "experience": 0.25},
    "fullstack":         {"coverage": 0.33, "semantic": 0.42, "experience": 0.25},
    "product":           {"coverage": 0.25, "semantic": 0.40, "experience": 0.35},
    "software_engineering": {"coverage": 0.40, "semantic": 0.40, "experience": 0.20},
}


def get_scorer_weights(domain: str) -> dict[str, float]:
    """Return component weights for scorer.py based on detected job domain."""
    return _DOMAIN_SCORER_WEIGHTS.get(domain, _DOMAIN_SCORER_WEIGHTS["software_engineering"])


# ΓöÇΓöÇ System prompt ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

_SYSTEM_PROMPT = """\
You are a constructive, state-of-the-art AI career coach conducting a holistic resume review.
You have been given:
  - The candidate's full resume text
  - A target job description
  - Pre-parsed metadata (experience years, education, certifications, formatting quality)
  - A list of skills explicitly missing from the resume

Your task: evaluate the resume across 5 independent dimensions and produce actionable improvement tips. Most importantly, provide a holistic `llm_ats_fit_score` (0-100) that mimics how advanced AI models like Claude or Gemini would score this candidate for the role (taking into account transferable skills, potential, and overall narrative, not just strict keyword matching).
Respond ONLY with a raw JSON object ΓÇö no markdown, no extra text.

JSON structure:
{
  "llm_ats_fit_score": <float 0-100>, // Holistic ATS fit score evaluating the candidate's true potential and alignment with the JD
  "dimension_scores": {
    "skills_match":  <float 0-10>,   // Match between resume skills and JD requirements
    "experience":    <float 0-10>,   // Depth, relevance, and years of work experience
    "education":     <float 0-10>,   // Degree relevance and institution prestige
    "projects":      <float 0-10>,   // Quality, complexity and relevance of projects
    "presentation":  <float 0-10>    // Clarity, formatting, quantified achievements
  },
  "improvement_tips": [
    {
      "category":       <"skills_match"|"experience"|"education"|"projects"|"presentation">,
      "issue_found":    <specific, concrete issue ΓÇö cite the actual resume text>,
      "actionable_fix": <step-by-step fix with examples ΓÇö not generic advice>,
      "impact":         <"high"|"medium"|"low">,
      "star_missing":   <true if this bullet/entry lacks a quantified Result>
    }
  ],
  "hr_red_flags": [
    <list of strings detailing critical HR red flags like unintentional age bias, vague wording, repetitive clichés, tone mismatches>
  ]
}

Scoring rubric:
- llm_ats_fit_score:
  - 90-100: Candidate meets all core tech requirements AND provides quantifiable metrics using the STAR framework (e.g., "Optimized ML pipeline latency by 40%").
  - 70-89: Candidate has the core tech stack but lacks metrics or impact statements.
  - Below 70: Candidate is missing primary technical skills.
- skills_match: 0-3 if major required skills absent; 4-6 if partial; 7-10 if strong match
- experience: Score based on how well the candidate's years of experience matches the Job Description. 0-3 if significantly below JD requirements; 4-7 if close; 8-10 if they meet or exceed the JD requirements. (Do NOT penalize students/fresh grads if the JD is for an entry-level/internship role).
- education: 0-3 if unrelated; 4-6 if partially relevant; 7-10 if directly relevant degree (NOTE: If the Job Description asks for a Diploma and the candidate possesses a higher degree like a B.Tech or M.Tech in the same field, you MUST count this as fully satisfying the educational requirement and score 7-10)
- projects: 0-3 if no/trivial projects; 4-6 if basic; 7-10 if impressive, relevant, quantified projects
- presentation: 0-3 if poorly structured; 4-6 if average; 7-10 if professional with metrics throughout

Rules:
- llm_ats_fit_score should be highly realistic but constructive. A great resume that misses a few keywords but shows strong transferable skills should score high (80-95). A completely irrelevant resume should score low (20-40).
- Score 9+ for dimensions only for exceptional candidates.
- Most candidates score 5-8 across dimensions.
- Generate between 2 to 7 high-impact actionable improvement tips. Do NOT arbitrarily generate exactly 1 tip per dimension. Focus only on the weakest areas that will actually move the needle.
- Every tip's actionable_fix MUST be specific to this resume ΓÇö not generic.
- Set star_missing=true for any experience bullet that describes a task without measuring its outcome.
- impact="high" if fixing this tip would boost ATS score by 10+ points.
- Identify "HR Red Flags" such as obvious grammar errors, extreme exaggerations, over-used buzzwords (e.g. "synergy"), or discriminatory/biased language.

---
FEW-SHOT EXAMPLES:

Example 1 (skills_match, high impact):
issue_found: "Resume lists 'Machine Learning' as a skill but never mentions PyTorch, TensorFlow, or scikit-learn, all of which are explicitly required in the JD."
actionable_fix: "1. Add a Technical Skills section at the top listing exact JD libraries: PyTorch, TensorFlow, scikit-learn. 2. In each relevant project bullet, name the library used: 'Built image classifier using PyTorch CNN achieving 94% accuracy on CIFAR-10.'"

Example 2 (experience, star_missing=true):
issue_found: "Intern role bullet reads 'Wrote code for backend endpoints' ΓÇö purely task-oriented with no outcome, scale, or metric."
actionable_fix: "Rewrite using the XYZ format: 'Designed and deployed 5 REST API endpoints in FastAPI, reducing average response time by 30% and enabling 2 new product features shipped to 10,000+ users.'"
"""


# ΓöÇΓöÇ Core LLM call ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def generate_strict_feedback(
    resume_text: str,
    job_description: str,
    missing_skills: list[str],
    user_id: Optional[str] = None,
    # Structured metadata from parser.py and quality_checker.py
    experience_years: float = 0.0,
    highest_degree: str = "",
    certifications: list[str] | None = None,
    formatting_score: float = 0.0,
    action_verb_rate: float = 0.0,
    quantification_rate: float = 0.0,
    sections_found: list[str] | None = None,
) -> tuple[ResumeFeedback, str, dict[str, float]]:
    """
    Evaluate the resume using the Groq LLM with structured context.

    Returns:
        (ResumeFeedback, detected_domain, scorer_component_weights)
        - ResumeFeedback        : Pydantic model with overall_score and improvement_tips
        - detected_domain       : str ΓÇö the auto-detected job domain
        - scorer_component_weights : dict for scorer.py component weighting
    """
    if not user_id:
        import hashlib
        user_id = hashlib.sha256(resume_text.encode("utf-8", errors="ignore")).hexdigest()

    domain = detect_job_domain(job_description)
    dim_weights = _DOMAIN_DIMENSION_WEIGHTS.get(domain, _DOMAIN_DIMENSION_WEIGHTS["software_engineering"])
    scorer_weights = get_scorer_weights(domain)

    # Build structured context block
    certs_str = ", ".join(certifications or []) or "None detected"
    sections_str = ", ".join(sections_found or []) or "Unknown"
    structured_context = (
        f"--- PRE-PARSED RESUME METADATA (use this as ground truth, do NOT guess) ---\n"
        f"Experience Years    : {experience_years:.1f} years\n"
        f"Highest Degree      : {highest_degree or 'Not detected'}\n"
        f"Certifications      : {certs_str}\n"
        f"Sections Found      : {sections_str}\n"
        f"Formatting Score    : {formatting_score:.1f}/10\n"
        f"  - Action Verb Rate    : {action_verb_rate*100:.0f}% of bullets start with a strong action verb\n"
        f"  - Quantification Rate : {quantification_rate*100:.0f}% of bullets contain a measurable metric\n"
        f"Skills Missing vs JD: {missing_skills}\n"
        f"Detected Job Domain : {domain}\n"
        f"Dimension Weights   : {dim_weights}\n"
        "---\n\n"
    )

    user_content = (
        "Please evaluate the following resume against the job description. "
        "You MUST output ONLY a valid JSON object. "
        "Use the pre-parsed metadata above as ground truth ΓÇö do NOT contradict it.\n\n"
        + structured_context
        + f"Target Job Description:\n{job_description or 'Not provided'}\n\n"
        + f"Candidate Resume:\n{resume_text[:6000]}\n\n"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            max_tokens=1500,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            user=user_id,
        )
    except Exception as e:
        print(f"[llm_engine] LLM call failed: {e}", file=sys.stderr)
        return _default_feedback(domain), domain, scorer_weights

    completion_msg = completion.choices[0].message
    if hasattr(completion_msg, "refusal") and completion_msg.refusal:
        print(f"[llm_engine] Model refused: {completion_msg.refusal}", file=sys.stderr)
        return _default_feedback(domain), domain, scorer_weights

    raw = completion_msg.content

    # ── Parse JSON Strictly with Pydantic ──
    try:
        # Pydantic structured output validation
        feedback = ResumeFeedback.model_validate_json(raw)
    except ValidationError as e:
        print(f"[llm_engine] Pydantic validation error: {e}\nRaw:\n{raw}", file=sys.stderr)
        return _default_feedback(domain), domain, scorer_weights
    except Exception as e:
        print(f"[llm_engine] JSON decode error: {e}\nRaw:\n{raw}", file=sys.stderr)
        return _default_feedback(domain), domain, scorer_weights

    # ── Compute weighted overall score in Python ──
    total_weight = 0.0
    weighted_sum = 0.0
    dim_scores = feedback.dimension_scores.model_dump()
    for key, weight in dim_weights.items():
        raw_score = dim_scores.get(key)
        if raw_score is not None:
            s = max(0.0, min(10.0, float(raw_score)))
            weighted_sum += s * weight
            total_weight += weight

    if total_weight > 0:
        feedback.overall_score = round(weighted_sum / total_weight, 1)
    else:
        feedback.overall_score = 0.0

    feedback.domain = domain

    # Sort tips by impact: high → medium → low
    _impact_order = {"high": 0, "medium": 1, "low": 2}
    feedback.improvement_tips.sort(key=lambda t: _impact_order.get(t.impact, 1))

    return feedback, domain, scorer_weights

def rewrite_resume(
    resume_text: str,
    job_description: str,
    missing_keywords: list[str],
    improvement_tips: list[dict],
    output_format: str = "tex",
) -> str:
    """
    Uses the Groq LLM to completely rewrite the candidate's resume.
    It injects missing keywords naturally and applies all formatting improvements.
    Returns standard Markdown or LaTeX.
    """
    ats_preservation_clause = """
CRITICAL ATS RULES (PENALTY FOR IGNORING):
1. You MUST PRESERVE all existing technical skills, tools, and keywords from the original resume. Do not delete them under any circumstances.
2. DO NOT HALLUCINATE FAKE WORK EXPERIENCE OR PROJECTS. Do NOT write completely fake job responsibilities or fake bullet points just to weave in missing keywords.
3. If you must add MISSING KEYWORDS to improve the ATS score, ONLY list them explicitly in the "Technical Skills" or "Skills" section. DO NOT invent fake job duties using skills the candidate never actually used.
"""

    if output_format in ["tex", "pdf"]:
        format_instructions = ats_preservation_clause + """
FORMATTING INSTRUCTIONS:
1. Output ONLY valid LaTeX code. Do NOT wrap it in markdown code blocks (e.g. no ```latex).
2. You MUST escape all LaTeX special characters (e.g., \\%, \\&, \\$, \\#, \\_). However, DO NOT use math mode (e.g. `$`, `\\sim`, `$<$`, `$>$`) for symbols like "approx" or "greater than". Instead, use plain text equivalents like "approx." or "over".
3. Use EXACTLY the following ATS-optimized LaTeX template structure. Fill in the bracketed placeholders with the optimized content:

\\documentclass[10pt,letterpaper]{article}
\\usepackage[left=0.5in, right=0.5in, top=0.5in, bottom=0.5in]{geometry}
\\usepackage{enumitem}
\\usepackage{titlesec}
\\usepackage{hyperref}

\\titleformat{\\section}{\\large\\bfseries\\uppercase}{}{0em}{}[\\titlerule]
\\titlespacing*{\\section}{0pt}{10pt}{5pt}
\\pagestyle{empty}

\\begin{document}
\\begin{center}
    {\\huge \\textbf{FULL NAME}} \\\\ \\vspace{2pt}
    Email | Phone | Location | LinkedIn | Portfolio
\\end{center}

\\section{Professional Summary}
[Impact-driven summary containing keywords]

\\section{Experience}
\\noindent \\textbf{Job Title} \\hfill Dates \\\\
\\textit{Company Name} \\hfill Location
\\begin{itemize}[leftmargin=*, parsep=0pt, itemsep=0pt]
    \\item [Impact-driven bullet point starting with Action Verb + Quantifiable Result]
\\end{itemize}

\\section{Projects}
\\noindent \\textbf{Project Name} \\hfill Dates
\\begin{itemize}[leftmargin=*, parsep=0pt, itemsep=0pt]
    \\item [Project detail]
\\end{itemize}

\\section{Education}
\\noindent \\textbf{Degree} \\hfill Dates \\\\
\\textit{University Name} \\hfill Location

\\section{Technical Skills}
\\begin{itemize}[leftmargin=*, parsep=0pt, itemsep=0pt]
    \\item \\textbf{Languages/Tools:} [All original skills + MISSING KEYWORDS]
\\end{itemize}

\\end{document}
"""
        sys_msg = "You are an elite Resume Writer. You strictly output raw LaTeX code using the exact template provided."
    else:
        format_instructions = ats_preservation_clause + """
FORMATTING INSTRUCTIONS:
1. Output ONLY valid Markdown. Do not include markdown code blocks.
2. Structure: Header, Professional Summary, Experience, Projects, Education, and Skills.
3. Rewrite bullet points to be impact-driven (Action Verb + Quantifiable Result), but only using the candidate's ACTUAL experience."""
        sys_msg = "You are an elite Resume Writer. You output perfectly formatted Markdown."

    prompt = f"""You are an elite Executive Resume Writer and ATS Optimization Expert.
Your task is to REWRITE the provided resume to perfectly align with the target Job Description.

TARGET JOB DESCRIPTION:
<job_description>
{job_description}
</job_description>

MISSING KEYWORDS TO INJECT NATURALLY:
{', '.join(missing_keywords) if missing_keywords else 'None'}

IMPROVEMENT TIPS TO APPLY:
{chr(10).join([f"- {t['actionable_fix']}" for t in improvement_tips]) if improvement_tips else 'None'}

ORIGINAL RESUME TEXT:
<original_resume>
{resume_text}
</original_resume>

INSTRUCTIONS:
{format_instructions}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": sys_msg
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=4000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[llm_engine] Error rewriting resume: {e}")
        return resume_text

def suggest_skill_integration(resume_text: str, skill: str) -> str:
    """
    Given a resume and a missing skill, suggests 1-2 ways to rewrite an existing bullet point
    to naturally include the skill. Uses llama-3.1-8b-instant for speed.
    """
    if not client:
        return "Please add this skill naturally to your most recent experience section."

    sys_msg = "You are an expert technical resume writer. Your job is to help a candidate naturally inject a missing skill into their resume."
    prompt = f"""
I have a resume, and it is missing the skill: "{skill}".

Please look at the resume text below and suggest EXACTLY ONE existing bullet point that could be rewritten to include this skill naturally.
Return your response in this exact format:
ORIGINAL: [paste the original bullet point here]
SUGGESTED REWRITE: [rewrite the bullet point to include the skill seamlessly, maintaining impact and metrics]

Do not include any other conversational text.

ORIGINAL RESUME TEXT:
{resume_text}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[llm_engine] Error suggesting skill integration: {e}")
        return "Please add this skill naturally to your most recent experience section."

def generate_json_edits(
    resume_text: str,
    job_description: str,
    missing_keywords: list[str],
    improvement_tips: list[dict],
) -> list[dict]:
    """
    Uses the 120B model to parse the resume and suggest line-by-line edits.
    Returns a list of dicts: {"original": "...", "suggested": "...", "reason": "..."}
    """
    if not client:
        return []

    sys_msg = "You are a world-class technical recruiter and resume writer. Return ONLY a pure JSON array."
    prompt = f"""
I need you to perform a line-by-line optimization of the following resume to better match the target job description.

TARGET JOB DESCRIPTION:
{job_description}

MISSING KEYWORDS TO INJECT:
{', '.join(missing_keywords) if missing_keywords else 'None'}

Please return a pure JSON array of objects. Each object represents ONE specific section or bullet point that you recommend changing.
Format:
[
  {{
    "original": "The exact original sentence or bullet point from the resume.",
    "suggested": "Your completely rewritten, optimized version incorporating keywords and action verbs.",
    "reason": "A very brief explanation of why this change improves the ATS score (e.g., 'Added AWS keyword')."
  }}
]

RULES:
1. ONLY return the JSON array. Do not include markdown code blocks like ```json.
2. Provide at least 3-5 high-impact bullet point rewrites.
3. Keep the "suggested" text completely ready to be copy-pasted (no meta-commentary inside the text).

ORIGINAL RESUME TEXT:
{resume_text}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4000,
        )
        content = response.choices[0].message.content.strip()
        # Clean markdown if present
        if content.startswith("```json"):
            content = content.replace("```json", "", 1).strip()
        if content.endswith("```"):
            content = content[:-3].strip()
            
        import json
        return json.loads(content)
    except Exception as e:
        error_msg = str(e)
        print(f"[llm_engine] Error generating JSON edits: {error_msg}")
        # If rate limit on 70b, retry with 8b model
        if "rate_limit_exceeded" in error_msg or "429" in error_msg:
            print("[llm_engine] Rate limit hit on 70b, falling back to 8b model...")
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=3000,
                )
                content = response.choices[0].message.content.strip()
                if content.startswith("```json"):
                    content = content.replace("```json", "", 1).strip()
                if content.endswith("```"):
                    content = content[:-3].strip()
                import json
                return json.loads(content)
            except Exception as e2:
                print(f"[llm_engine] 8b fallback also failed: {e2}")
        return []

def format_to_latex(resume_text: str) -> str:
    """
    Uses the 8B model to format plain text into an ATS-friendly LaTeX resume.
    """
    if not client:
        return resume_text
        
    prompt = f"""
Convert the following plain text resume into a professional, ATS-friendly LaTeX format.
DO NOT rewrite the text. ONLY apply the LaTeX formatting.
Escape all special characters. Output ONLY the LaTeX code.

RESUME TEXT:
{resume_text}
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=4000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[llm_engine] Error formatting to latex: {e}")
        return resume_text
