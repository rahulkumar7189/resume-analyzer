import os
import time
import json
import pathlib
import hashlib
from typing import Optional
from api.celery_app import celery_app
from api.redis_client import set_cached_result

# ML Pipeline imports
from src.extractor import extract_text, extract_skills_section_aware
from src.scorer import calculate_ats_match, _build_expanded_resume_set, _clean_jd_skill_key
from src.llm_engine import generate_strict_feedback, detect_job_domain, get_scorer_weights, client as groq_client
from src.parser import parse_resume, extract_jd_required_degree, evaluate_education_fit
from src.quality_checker import check_formatting
from src.llm_engine import rewrite_resume
from src.document_generator import markdown_to_docx
parent_dir = str(pathlib.Path(__file__).resolve().parent.parent)

def _get_db_connection():
    try:
        import psycopg2
        return psycopg2.connect(
            dbname=os.getenv("DB_NAME", "ats_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "root"),
            host=os.getenv("DB_HOST", "db"), # In docker it will be 'db', locally 'localhost'.
            port=os.getenv("DB_PORT", "5432")
        )
    except Exception as e:
        print(f"[tasks] DB connection failed: {e}")
        return None

@celery_app.task(bind=True)
def process_resume_task(
    self, 
    resume_text: str, 
    resume_filename: str, 
    job_description: str, 
    metadata: dict,
    resume_url: str,
    job_id: Optional[str] = None, 
    recruiter_id: Optional[str] = None,
    cache_key: Optional[str] = None
):
    """
    Celery task that runs the heavy NLP pipeline in the background.
    """
    name = metadata["name"]
    email = metadata["email"]
    social_links = metadata["social_links"]
    
    print(f"[tasks] Starting processing for {name}")
    
    try:
        # 1. Structured resume parsing
        parsed = parse_resume(resume_text)
        sections = parsed.sections
        experience_years = parsed.experience_years
        highest_degree = parsed.highest_degree
        certifications = parsed.certifications
        sections_found = list(sections.keys())
        
        # 2. Formatting quality check
        exp_section_text = sections.get("EXPERIENCE", "") + "\n" + sections.get("PROJECTS", "")
        formatting_score_obj = check_formatting(resume_text, exp_section_text, sections_found=sections_found, metadata=metadata)
        action_verb_rate = formatting_score_obj.action_verb_rate
        quantification_rate = formatting_score_obj.quantification_rate
        formatting_score_val = formatting_score_obj.overall_formatting_score
        formatting_data = {
            "overall_score": formatting_score_val,
            "action_verb_rate": round(action_verb_rate * 100, 1),
            "quantification_rate": round(quantification_rate * 100, 1),
            "total_bullets": formatting_score_obj.total_bullets,
            "estimated_pages": formatting_score_obj.estimated_pages,
            "ats_warnings": formatting_score_obj.ats_format_warnings,
            "parsability_score": formatting_score_obj.parsability_score,
            "completeness_warnings": formatting_score_obj.completeness_warnings,
            "weak_verb_examples": formatting_score_obj.weak_verb_examples,
            "strong_verb_examples": formatting_score_obj.strong_verb_examples,
            "quantified_examples": formatting_score_obj.quantified_examples,
        }
        
        # 3. Section-aware skill extraction
        user_hash = hashlib.sha256(email.encode("utf-8", errors="ignore")).hexdigest()
        resume_skills, skills_by_section = extract_skills_section_aware(resume_text, sections)
        
        # 4. LLM feedback
        detected_domain = detect_job_domain(job_description)
        scorer_weights = get_scorer_weights(detected_domain)
        
        ats_score, missing_skills, keyword_match_detail = calculate_ats_match(
            extracted_resume_skills=resume_skills,
            job_description_text=job_description,
            llm_client=groq_client,
            user_id=user_hash,
            resume_experience_months=parsed.total_experience_months,
            skills_by_section=skills_by_section,
            domain_weights=scorer_weights,
        )
        
        feedback, detected_domain, scorer_weights = generate_strict_feedback(
            resume_text=resume_text,
            job_description=job_description,
            missing_skills=missing_skills,
            user_id=user_hash,
            experience_years=experience_years,
            highest_degree=highest_degree,
            certifications=certifications,
            formatting_score=formatting_score_val,
            action_verb_rate=action_verb_rate,
            quantification_rate=quantification_rate,
            sections_found=sections_found,
        )
        
        llm_holistic = float(feedback.overall_score) * 10.0
        
        # 1. Resume Health Score (Formatting + Impact + LLM Holistic)
        # This is strictly how GOOD the resume is, regardless of the job it is applying to.
        resume_health_score = round((formatting_score_val * 10.0) * 0.60 + llm_holistic * 0.40, 1)
        resume_health_score = max(0.0, min(100.0, resume_health_score))
        
        # 2. Job Match Fit Score (Exponential Non-Linear Gating)
        # This is how well the resume matches the target JD.
        llm_fit = getattr(feedback, "llm_ats_fit_score", ats_score)
        
        # Educational Pre-processing Step
        jd_req_degree = extract_jd_required_degree(job_description)
        edu_fit_score = evaluate_education_fit(highest_degree, jd_req_degree) * 100.0
        
        # Blend education normalization into the mechanical score before gating
        ats_score_blended = ats_score * 0.85 + edu_fit_score * 0.15
        
        # Non-linear exponential gating modifier
        # Final Score = LLM Score * (Mechanical Score / 100) ^ 0.4
        penalty_multiplier = (ats_score_blended / 100.0) ** 0.4
        job_match_score = llm_fit * penalty_multiplier
            
        job_match_score = round(max(0.0, min(100.0, job_match_score)), 1)
        
        # Build matched vs missing skills
        if keyword_match_detail:
            matched_skills = [kd["keyword"] for kd in keyword_match_detail if kd["found"]]
            jd_keywords_lower = {kd["keyword"].lower() for kd in keyword_match_detail}
            extra = [s for s in resume_skills if s.lower() not in jd_keywords_lower]
            matched_skills = matched_skills + extra
        else:
            matched_skills = resume_skills[:]
            
        result_data = {
            "ats_score": job_match_score, # Legacy field, kept for backwards compatibility
            "resume_health_score": resume_health_score,
            "job_match_score": job_match_score,
            "domain": detected_domain,
            "extracted_skills": {
                "matched": matched_skills,
                "missing": missing_skills,
                "by_section": {k: v for k, v in skills_by_section.items() if k not in ("HEADER",)},
            },
            "keyword_match_detail": keyword_match_detail,
            "improvement_tips": [
                {
                    "category": tip.category,
                    "issue_found": tip.issue_found,
                    "actionable_fix": tip.actionable_fix,
                    "impact": tip.impact,
                    "star_missing": tip.star_missing,
                }
                for tip in feedback.improvement_tips
            ],
            "hr_red_flags": feedback.hr_red_flags,
            "candidate_name": name,
            "candidate_email": email,
            "resume_url": resume_url,
            "social_links": social_links,
            "experience_years": experience_years,
            "highest_degree": highest_degree,
            "certifications": certifications,
            "sections_found": sections_found,
            "education": [
                {
                    "degree_type": e.degree_type,
                    "field": e.field,
                    "institution": e.institution,
                    "graduation_year": e.graduation_year,
                    "gpa": e.gpa,
                }
                for e in parsed.education
            ],
            "formatting": formatting_data,
        }
        
        # 6. Save to DB
        conn = _get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO public.resume_scans (
                            candidate_name, candidate_email, ats_score, extracted_skills,
                            improvement_tips, job_description, resume_url, social_links,
                            job_id, recruiter_id, experience_years, highest_degree,
                            certifications, domain, formatting
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            name, email, result_data["ats_score"],
                            json.dumps(result_data["extracted_skills"]),
                            json.dumps(result_data["improvement_tips"]),
                            job_description, resume_url,
                            json.dumps(social_links),
                            job_id or None, recruiter_id or None,
                            result_data["experience_years"], result_data["highest_degree"],
                            json.dumps(result_data["certifications"]), result_data["domain"],
                            json.dumps(result_data["formatting"])
                        )
                    )
                    conn.commit()
            except Exception as e:
                print(f"[tasks] DB write failed: {e}")
            finally:
                conn.close()
                
        if cache_key:
            set_cached_result(cache_key, result_data)
                
        return {"status": "success", "data": result_data}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "detail": str(e)}

@celery_app.task(bind=True)
def autofix_resume_task(
    self,
    resume_url: str,
    job_description: str,
    missing_keywords: list,
    improvement_tips: list,
    output_format: str = "tex"
):
    """
    Auto-fixes a resume by rewriting it with the LLM and generating a DOCX, TEX, or MD file.
    """
    try:
        # Load the original text
        file_path = pathlib.Path(parent_dir) / "ats-web" / "public" / resume_url.lstrip("/")
        if not file_path.exists():
            return {"status": "error", "detail": "Original resume file not found."}
            
        # Parse original text
        from api.main import _parse_pdf, _parse_docx
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            resume_text = _parse_pdf(str(file_path))
        elif ext == ".docx":
            resume_text = _parse_docx(str(file_path))
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                resume_text = f.read()
                
        # Call LLM to rewrite
        rewritten_md = rewrite_resume(resume_text, job_description, missing_keywords, improvement_tips, output_format)
        
        # Prepare upload dir
        upload_dir = pathlib.Path(parent_dir) / "ats-web" / "public" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        unique_name = f"optimized_{int(time.time())}.{output_format}"
        save_path = upload_dir / unique_name
        
        if output_format == "docx":
            markdown_to_docx(rewritten_md, str(save_path))
        elif output_format == "pdf":
            # Save as temporary .tex file to compile
            tex_path = upload_dir / f"optimized_{int(time.time())}.tex"
            with open(tex_path, "w", encoding="utf-8") as f:
                import re
                # Extract everything from \documentclass to \end{document}
                match = re.search(r'\\documentclass.*\\end\{document\}', rewritten_md, re.DOTALL)
                if match:
                    clean_latex = match.group(0)
                else:
                    # Fallback if the regex fails
                    clean_latex = rewritten_md.replace("```latex", "").replace("```", "").strip()
                    
                # Programmatically ensure special characters are escaped (since the 8B model sometimes forgets)
                # Escape & if not already escaped
                clean_latex = re.sub(r'(?<!\\)&', r'\\&', clean_latex)
                # Escape % if not already escaped (except for any legitimate LaTeX comments, but we don't expect any from the LLM)
                clean_latex = re.sub(r'(?<!\\)%', r'\\%', clean_latex)
                # Hard strip out illegal math commands that the LLM sometimes hallucinates
                clean_latex = clean_latex.replace(r'\$\sim\$', 'approx. ').replace(r'$\sim$', 'approx. ').replace(r'\sim', 'approx. ')
                clean_latex = clean_latex.replace(r'\$>\$', 'over ').replace(r'$>$', 'over ')
                clean_latex = clean_latex.replace(r'\$<$', 'under ').replace(r'$<$', 'under ')
                # Remove uncompilable Unicode spaces
                clean_latex = clean_latex.replace('\u202F', ' ').replace('\u200B', '').replace('\u00A0', ' ')
                # Replace uncompilable Unicode hyphens/dashes
                clean_latex = clean_latex.replace('\u2011', '-').replace('\u2013', '--').replace('\u2014', '---')
                # Replace smart quotes
                clean_latex = clean_latex.replace('\u2018', "'").replace('\u2019', "'").replace('\u201C', '"').replace('\u201D', '"')
                
                f.write(clean_latex)
            
            import subprocess
            try:
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(upload_dir), str(tex_path)],
                    check=True,
                    capture_output=True
                )
                pdf_name = tex_path.stem + ".pdf"
                unique_name = pdf_name
            except subprocess.CalledProcessError as e:
                print(f"pdflatex error: {e.output.decode('utf-8', errors='replace')}")
                return {"status": "error", "detail": "Failed to compile PDF. There might be a LaTeX syntax error."}
        else:
            with open(save_path, "w", encoding="utf-8") as f:
                # Clean up if the LLM output markdown codeblocks
                clean_text = rewritten_md.replace("```latex", "").replace("```markdown", "").replace("```", "").strip()
                f.write(clean_text)
        
        new_resume_url = f"/uploads/{unique_name}"
        return {"status": "success", "new_resume_url": new_resume_url}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "detail": str(e)}

@celery_app.task(bind=True)
def suggest_edits_task(
    self,
    resume_url: str,
    job_description: str,
    missing_keywords: list,
    improvement_tips: list
):
    """
    Parses the original resume and uses the LLM to generate a JSON array of line-by-line edit suggestions.
    """
    try:
        file_path = pathlib.Path(parent_dir) / "ats-web" / "public" / resume_url.lstrip("/")
        if not file_path.exists():
            return {"status": "error", "detail": "Original resume file not found."}
            
        from api.main import _parse_pdf, _parse_docx
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            resume_text = _parse_pdf(str(file_path))
        elif ext == ".docx":
            resume_text = _parse_docx(str(file_path))
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                resume_text = f.read()
                
        from src.llm_engine import generate_json_edits
        edits = generate_json_edits(resume_text, job_description, missing_keywords, improvement_tips)
        
        return {"status": "success", "edits": edits}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "detail": str(e)}

@celery_app.task(bind=True)
def compile_pdf_task(self, resume_url: str, accepted_edits: list[dict], template: str = "modern"):
    import time
    try:
        file_path = pathlib.Path(parent_dir) / "ats-web" / "public" / resume_url.lstrip("/")
        if not file_path.exists():
            return {"status": "error", "detail": "Original resume file not found."}
            
        from api.main import _parse_pdf, _parse_docx
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            resume_text = _parse_pdf(str(file_path))
        elif ext == ".docx":
            resume_text = _parse_docx(str(file_path))
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                resume_text = f.read()
                
        # Apply edits
        import re
        updated_text = resume_text
        for edit in accepted_edits:
            original = edit.get("original", "")
            suggested = edit.get("suggested", "")
            if original and suggested:
                # Extract all alphanumeric words from the original text
                words = re.findall(r'[a-zA-Z0-9]+', original)
                if words:
                    # Build a pattern that allows ANY non-alphanumeric characters (spaces, newlines, hyphens, dashes) between words
                    pattern = r'\W+'.join(re.escape(w) for w in words)
                    updated_text = re.sub(pattern, suggested, updated_text, count=1, flags=re.IGNORECASE)
                
        # Parse structured resume data and render chosen LaTeX template
        from src.resume_section_parser import parse_resume_text
        from src.latex_templates import render_template
        resume_data = parse_resume_text(updated_text)
        latex_code = render_template(template, resume_data)
        
        # Save and compile
        upload_dir = pathlib.Path(parent_dir) / "ats-web" / "public" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        tex_path = upload_dir / f"compiled_{int(time.time())}.tex"
        
        import re
        # Clean any stray code fences if they sneaked in
        latex_code = latex_code.replace("```latex", "").replace("```", "").strip()
        
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_code)
            
        import subprocess
        try:
            # First pass
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(upload_dir), str(tex_path)],
                check=True,
                capture_output=True
            )
            # Second pass for absolute positioning
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(upload_dir), str(tex_path)],
                check=True,
                capture_output=True
            )
            pdf_name = tex_path.stem + ".pdf"
            return {"status": "success", "new_resume_url": f"/uploads/{pdf_name}"}
        except subprocess.CalledProcessError as e:
            print(f"pdflatex error: {e.output.decode('utf-8', errors='replace')}")
            return {"status": "error", "detail": "Failed to compile PDF. There might be a LaTeX syntax error."}
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "detail": str(e)}
