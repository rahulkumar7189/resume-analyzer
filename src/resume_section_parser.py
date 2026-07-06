"""
resume_section_parser.py
------------------------
Parses plain resume text into structured sections for Jinja2 template rendering.
Uses LLM-based extraction via Groq for structured JSON parsing.
"""
from __future__ import annotations
import json
import logging
from src.llm_engine import client

logger = logging.getLogger(__name__)

_JSON_EXTRACT_PROMPT = """\
You are an expert resume parser. Extract the provided raw resume text into a strict JSON object matching the exact schema below.
DO NOT summarize or change the bullet points. Copy them exactly as they appear. If a section is missing, use empty arrays/strings.
For "projects", if a project doesn't have a title, use a short descriptive phrase.

SCHEMA:
{
  "name": "string",
  "email": "string",
  "phone": "string",
  "linkedin": "string",
  "github": "string",
  "location": "string",
  "summary": "string",
  "experience": [
    {
      "title": "string",
      "company": "string",
      "dates": "string",
      "bullets": ["string"]
    }
  ],
  "education": [
    {
      "degree": "string",
      "institution": "string",
      "dates": "string",
      "details": ["string"]
    }
  ],
  "projects": [
    {
      "title": "string",
      "bullets": ["string"]
    }
  ],
  "skills": {
    "Languages": ["string"],
    "Frameworks": ["string"],
    "Tools": ["string"]
  },
  "certifications": ["string"]
}

Respond ONLY with valid JSON. No markdown formatting or extra text.
"""

def parse_resume_text(text: str) -> dict:
    """
    Parses unstructured resume text into a strict JSON dictionary using Llama 3.1 8B.
    """
    from src.latex_templates import _escape
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": _JSON_EXTRACT_PROMPT},
                {"role": "user", "content": f"Extract the following resume text:\n\n{text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=4000,
        )
        
        raw_json = response.choices[0].message.content
        data = json.loads(raw_json)
    except Exception as e:
        logger.error(f"Failed to parse resume with LLM: {e}")
        # Fallback empty structure
        data = {
            "name": "Candidate", "email": "", "phone": "", "linkedin": "", "github": "", "location": "",
            "summary": "Failed to parse resume sections.", "experience": [], "education": [], "projects": [],
            "skills": {}, "certifications": []
        }

    # Escape everything for LaTeX
    def esc_list(items: list[str]) -> list[str]:
        return [_escape(i) for i in items]
    
    def esc_exp(jobs: list[dict]) -> list[dict]:
        return [{
            "title": _escape(j.get("title", "")),
            "company": _escape(j.get("company", "")),
            "dates": _escape(j.get("dates", "")),
            "bullets": esc_list(j.get("bullets", [])),
        } for j in jobs]
        
    def esc_proj(projects: list[dict]) -> list[dict]:
        return [{
            "title": _escape(p.get("title", "")),
            "bullets": esc_list(p.get("bullets", [])),
        } for p in projects]
    
    def esc_edu(items: list[dict]) -> list[dict]:
        return [{
            "degree": _escape(e.get("degree", "")),
            "institution": _escape(e.get("institution", "")),
            "dates": _escape(e.get("dates", "")),
            "details": esc_list(e.get("details", [])),
        } for e in items]
    
    def esc_skills(d: dict) -> dict:
        return {_escape(str(k)): [_escape(v) for v in vals] for k, vals in d.items()}

    return {
        "name": _escape(data.get("name", "Candidate")),
        "email": _escape(data.get("email", "")),
        "phone": _escape(data.get("phone", "")),
        "linkedin": data.get("linkedin", ""),   # URLs: don't escape
        "github": data.get("github", ""),
        "location": _escape(data.get("location", "")),
        "summary": _escape(data.get("summary", "")),
        "experience": esc_exp(data.get("experience", [])),
        "education": esc_edu(data.get("education", [])),
        "projects": esc_proj(data.get("projects", [])),
        "skills": esc_skills(data.get("skills", {})),
        "certifications": esc_list(data.get("certifications", [])),
    }
