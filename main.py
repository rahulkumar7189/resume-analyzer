# main.py – entry point for PDF resume analysis using Groq LLM
"""Usage:
    python main.py <pdf_path> [--job "Job description text"] [--missing "skill1,skill2,..."]

The script extracts plain text from the given PDF (using PyPDF2), then calls
`generate_strict_feedback` from `src.llm_engine` to obtain a structured
`ResumeFeedback` object and prints it as JSON.

Requirements:
    - PyPDF2 (`pip install PyPDF2`)
    - spacy (already in the project)
    - The Groq API key is embedded in `src/llm_engine.py`.
"""
import argparse
import json
import pathlib
import sys
from typing import List

# PDF extraction – we use PyPDF2 because it is lightweight and works on Windows.
try:
    from PyPDF2 import PdfReader
except ImportError:
    print("PyPDF2 is required. Install it with: pip install PyPDF2", file=sys.stderr)
    sys.exit(1)

# Import the LLM helper from our src package.
# The project root (d:/NLP) is on the Python path when we run from that directory,
# so we can import using a relative package import.
from src.llm_engine import generate_strict_feedback, ResumeFeedback, client as groq_client
from src.scorer import calculate_ats_match
from src.extractor import extract_text, extract_skills_locally


def extract_text_from_pdf(pdf_path: pathlib.Path) -> str:
    """Extract plain text from a PDF file.

    Args:
        pdf_path: Path to the PDF document.
    Returns:
        A single string containing the concatenated text of all pages.
    """
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    reader = PdfReader(str(pdf_path))
    texts = []
    for page_num, page in enumerate(reader.pages, start=1):
        try:
            texts.append(page.extract_text() or "")
        except Exception as e:
            print(f"Warning: could not extract page {page_num}: {e}", file=sys.stderr)
    return "\n".join(texts)


def parse_missing_skills(arg: str) -> List[str]:
    """Convert a comma‑separated string into a list of skill strings."""
    if not arg:
        return []
    return [skill.strip() for skill in arg.split(",") if skill.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate structured feedback for a resume PDF using Groq.")
    parser.add_argument("pdf_path", type=pathlib.Path, help="Path to the PDF file containing the resume.")
    parser.add_argument("--job", type=str, default="", help="Job description text (paste directly from LinkedIn/Naukri).")
    parser.add_argument("--job-file", type=pathlib.Path, default=None, help="Path to a .txt file containing the job description (useful for long JDs).")
    parser.add_argument(
        "--missing",
        type=str,
        default="",
        help="Comma‑separated list of missing skills to highlight in the feedback.",
    )
    args = parser.parse_args()

    # Resolve job description — prefer --job-file over --job
    job_desc = ""
    if args.job_file:
        if not args.job_file.is_file():
            print(f"Error: job file not found: {args.job_file}", file=sys.stderr)
            sys.exit(1)
        job_desc = args.job_file.read_text(encoding="utf-8").strip()
        print(f"Loaded job description from: {args.job_file} ({len(job_desc)} chars)")
    elif args.job:
        job_desc = args.job.strip()
    else:
        print("Warning: No job description provided. Scores will be less accurate. Use --job or --job-file.", file=sys.stderr)


    # 1️⃣ Extract raw text from the PDF.
    resume_text = extract_text_from_pdf(args.pdf_path)
    if not resume_text.strip():
        print("No extractable text found in the PDF.", file=sys.stderr)
        sys.exit(1)

    # 2️⃣ Extract skills from the resume using Hybrid NER
    print("[*] Extracting skills from resume...")
    resume_skills = extract_skills_locally(resume_text)
    print(f"    Found {len(resume_skills)} skills: {resume_skills[:10]}{'...' if len(resume_skills) > 10 else ''}")

    # 3a. Use caller-provided missing skills list, or auto-compute from JD
    if args.missing.strip():
        missing_skills = parse_missing_skills(args.missing)
    elif job_desc:
        print("[*] Computing ATS match score with semantic + LLM skill weighting...")
        _match_score, missing_skills = calculate_ats_match(resume_skills, job_desc, groq_client)
        print(f"    ATS Match Score: {_match_score}%")
        print(f"    Missing skills : {missing_skills}")
    else:
        missing_skills = []


    # 3️⃣ Call the Groq LLM helper.
    try:
        feedback: ResumeFeedback = generate_strict_feedback(resume_text, job_desc, missing_skills)
    except Exception as e:
        print(f"Error during LLM call: {e}", file=sys.stderr)
        sys.exit(1)

    # 4️⃣ Output the feedback as pretty‑printed JSON.
    print(json.dumps(feedback.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
