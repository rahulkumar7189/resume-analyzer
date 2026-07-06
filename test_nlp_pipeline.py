"""
Quick integration test for the new NLP pipeline.
Run from the project root:
    python test_nlp_pipeline.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

PDF_PATH = "src/122.pdf"
JD_TEXT = """
We are looking for a Senior Machine Learning Engineer with 3+ years of experience.
Required: Python, PyTorch, TensorFlow, scikit-learn, Docker, Kubernetes, AWS, FastAPI.
Experience with LLMs, RAG, LangChain, and vector databases like Pinecone or ChromaDB is a strong plus.
Bachelor's or Master's degree in Computer Science, Data Science, or related field.
"""

print("=" * 60)
print("TEST 1 — PDF text extraction")
print("=" * 60)
from src.extractor import extract_text
text = extract_text(PDF_PATH)
print(f"  Extracted {len(text)} chars, {len(text.split())} words")
print(f"  First 200 chars: {text[:200].strip()!r}")

print()
print("=" * 60)
print("TEST 2 — Resume section segmentation")
print("=" * 60)
from src.parser import parse_resume, segment_sections
sections = segment_sections(text)
print(f"  Sections found: {list(sections.keys())}")
for sec, content in sections.items():
    print(f"    [{sec}] {len(content)} chars")

print()
print("=" * 60)
print("TEST 3 — Full structured parse")
print("=" * 60)
parsed = parse_resume(text)
print(f"  Experience entries: {len(parsed.experience)}")
print(f"  Total experience  : {parsed.experience_years} years ({parsed.total_experience_months} months)")
print(f"  Education entries : {len(parsed.education)}")
for edu in parsed.education:
    print(f"    {edu.degree_type} in {edu.field or 'N/A'} @ {edu.institution or 'N/A'} ({edu.graduation_year})")
print(f"  Certifications    : {parsed.certifications}")
print(f"  Contact name      : {parsed.contact.name!r}")
print(f"  Contact email     : {parsed.contact.email!r}")
print(f"  GitHub            : {parsed.contact.github!r}")
print(f"  LinkedIn          : {parsed.contact.linkedin!r}")
print(f"  Highest degree    : {parsed.highest_degree!r}")

print()
print("=" * 60)
print("TEST 4 — Formatting quality check")
print("=" * 60)
from src.quality_checker import check_formatting
fmt = check_formatting(text, sections.get("EXPERIENCE", ""))
print(f"  Overall formatting score : {fmt.overall_formatting_score}/10")
print(f"  Total bullets            : {fmt.total_bullets}")
print(f"  Action verb rate         : {fmt.action_verb_rate:.0%}")
print(f"  Quantification rate      : {fmt.quantification_rate:.0%}")
print(f"  Estimated pages          : {fmt.estimated_pages}")
print(f"  ATS warnings             : {fmt.ats_format_warnings}")
if fmt.weak_verb_examples:
    print(f"  Weak verb examples       : {fmt.weak_verb_examples[:2]}")
if fmt.strong_verb_examples:
    print(f"  Strong verb examples     : {fmt.strong_verb_examples[:2]}")

print()
print("=" * 60)
print("TEST 5 — Section-aware skill extraction")
print("=" * 60)
from src.extractor import extract_skills_section_aware
skills, by_section = extract_skills_section_aware(text, sections)
print(f"  Total skills found: {len(skills)}")
print(f"  Skills: {skills[:20]}")
print(f"  By section:")
for sec, sec_skills in by_section.items():
    print(f"    [{sec}]: {sec_skills[:5]}")

print()
print("=" * 60)
print("TEST 6 — Domain detection")
print("=" * 60)
from src.llm_engine import detect_job_domain, get_scorer_weights
domain = detect_job_domain(JD_TEXT)
weights = get_scorer_weights(domain)
print(f"  Detected domain  : {domain}")
print(f"  Scorer weights   : {weights}")

print()
print("=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)
