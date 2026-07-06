# 🔍 ATS Project — Complete Gap Analysis

A professional resume analyzer must do far more than keyword matching and a single LLM call. Here is every gap found across all three layers, ordered by severity.

---

## 🧠 NLP / Core Engine Gaps — (Most Critical)

These are the gaps that make or break the quality of a "professional" ATS analyzer.

### ❌ 1. No Resume Section Segmentation
**What's missing:** The entire resume is currently processed as a single blob of text. A professional ATS parses it into distinct **sections**: `CONTACT`, `SUMMARY`, `EDUCATION`, `WORK EXPERIENCE`, `PROJECTS`, `SKILLS`, `CERTIFICATIONS`, `AWARDS`, `PUBLICATIONS`.

**Why it matters:** Without segmentation:
- Work experience years cannot be counted accurately.
- Skills listed in a "Projects" section are treated the same as skills from "5 years at Google".
- Education details (degree, institution, GPA) cannot be evaluated independently.
- The LLM is forced to guess structure from raw text, introducing hallucination risk.

**Professional standard:**
```
Raw Text → Section Detector (regex + ML) → Structured Resume Object
          {contact, summary, education[], experience[], projects[], skills[], certs[]}
```

---

### ❌ 2. No Experience Date Parsing / Years of Experience Calculation
**What's missing:** The backend never computes **total years of relevant experience**. It sends raw text to the LLM and hopes it estimates correctly.

**Why it matters:** A job requiring "5+ years of Python" cannot be objectively evaluated without parsing `Jan 2020 – May 2024` date ranges and computing durations. LLMs are unreliable for this.

**Missing logic:**
- Parse start/end date strings (`Jun 2019 – Present`, `2021 – 2023`)
- Compute total months/years per role
- Map each role's skills to extracted skills from that role
- Calculate total experience per technology

---

### ❌ 3. No Education Tier / Degree Recognition
**What's missing:** No structured extraction of:
- Degree type (`B.Tech`, `M.Sc`, `PhD`, `MBA`, `Diploma`)
- Field of study (`Computer Science`, `Electrical Engineering`, `MBA`)
- Institution (for reputation scoring)
- GPA (if present)
- Graduation year (to estimate seniority)

Currently the LLM guesses all of this. There is no structured ground truth to validate its guess.

---

### ❌ 4. No Resume Formatting / Structure Quality Check
**What's missing:** A professional ATS checks:
- **Bullet point quality** — are bullets action-verb-led? ("Developed" not "Responsible for")
- **Quantification rate** — what percentage of bullet points contain numbers/metrics?
- **Length** — is the resume 1-2 pages or 5 pages?
- **ATS-incompatible formatting** — tables, columns, text boxes, images (these break real-world ATS parsers)
- **Keyword stuffing** — detecting unnatural keyword density
- **Whitespace / section header clarity**

None of this is checked programmatically. It is only loosely covered by a general LLM prompt.

---

### ❌ 5. Skill Extraction Is Too Shallow for ML/AI Roles
**What's missing:** The `CANONICAL_SKILLS` list in `skills_db.py` is good but has significant blind spots:

| Category | Missing Examples |
|---|---|
| Cloud Certifications | `AWS Certified Solutions Architect`, `GCP Professional Data Engineer` |
| Modern AI | `Claude`, `Gemini API`, `Mistral`, `Ollama`, `vLLM`, `Axolotl`, `LoRA fine-tuning` |
| Data roles | `dbt Core`, `Great Expectations`, `Delta Lake`, `Iceberg`, `Apache Flink` |
| System Design | `Load Balancing`, `Caching`, `Rate Limiting`, `CAP Theorem`, `Distributed Systems` |
| Soft skills (structured) | `Team Leadership`, `Cross-functional Collaboration`, `Technical Mentoring` |
| Languages (missing) | `Zig`, `Nim`, `Crystal`, `Mojo` |

More critically, the `EntityRuler` only matches **exact token strings**. A resume listing `"built ML pipelines using py-torch"` (hyphenated) will NOT match `PyTorch`.

---

### ❌ 6. No Semantic Role-Skill Matching (Contextual Skill Validation)
**What's missing:** Currently, if a resume mentions Python, it counts as a Python skill — regardless of whether it's in a "Hobbies" section or a "Senior Engineer" role. 

A professional ATS validates **context**:
- Was the skill used in a professional or academic setting?
- How many years of practice is demonstrated?
- Is the skill used alongside other related skills (indicating depth)?

This requires section-aware skill extraction, not global text scanning.

---

### ❌ 7. Keyword Density Analysis Against JD Is Missing
**What's missing:** The system computes a single similarity score. A real ATS does **keyword-by-keyword matching**:
- Which exact JD keywords appear in the resume?
- Which section do they appear in?
- Do they appear in the first half of the resume (higher visibility for parsers)?
- Are action verbs from the JD mirrored in the resume?

This granular breakdown lets candidates know exactly WHICH words to add and WHERE.

---

### ❌ 8. No STAR Format Detection for Experience Bullets
**What's missing:** Professional resume analyzers check if experience bullets follow the **STAR** (Situation → Task → Action → Result) or **XYZ** (Accomplished X by doing Y resulting in Z) formats. Currently only the LLM loosely evaluates this in a generic tip.

---

### ❌ 9. No Certifications / Awards Extraction
**What's missing:** Certifications are extremely important for ATS scoring in many domains (Cloud, Project Management, Security). There is no structured extraction of:
- Certification names (`AWS SAA-C03`, `PMP`, `CEH`, `CKA`)
- Issuing organization
- Issue date / expiry

---

### ❌ 10. No Industry-Specific Score Weighting
**What's missing:** The 5-dimension scoring (skills 30%, experience 25%, etc.) uses fixed weights. But a **Data Science** role should weight projects and education differently than a **DevOps** role. The system should detect the job domain and adjust weights accordingly.

---

### ❌ 11. Scoring Blend Is Arbitrary (40% keyword + 60% LLM)
**Current code in `api/main.py`:**
```python
final_ats_score = round((keyword_score * 0.4) + (llm_score * 0.6), 1)
```
**Problem:** This is a hardcoded magic number with no research backing. The keyword score from `scorer.py` uses semantic embeddings (cosine similarity of skill strings) and the LLM gives a holistic review. These are not on the same scale and cannot be linearly blended this naively. The result is an ATS score that is difficult to explain or validate.

---

### ❌ 12. No Resume vs Resume Comparative Benchmarking (Recruiter Mode)
**What's missing:** In recruiter mode, candidates are ranked by absolute score. A professional ATS would also show:
- How candidates compare to each other per skill category
- A benchmark against an "ideal candidate" score
- Outlier detection (a candidate who excels in one area but fails in others)

---

## ⚙️ Backend / API Gaps

### ❌ 13. `proxy.ts` is NOT an actual Next.js Middleware
**Critical bug:** The routing/auth guard logic lives in `src/proxy.ts`. Next.js only executes `middleware.ts` at the `src/` root level. This file is currently **dead code** — any user can access `/recruiter` or `/candidate` without being logged in.

**Fix:** Rename `proxy.ts` → `middleware.ts`.

---

### ❌ 14. Jobs Are Not Persisted to Supabase
**What's missing:** Job posts in the recruiter dashboard are stored only in React state (`useState`). When the page refreshes, all jobs disappear.

**What's needed:** A `jobs` table in Supabase to CRUD job postings, along with linking each `resume_scan` to the corresponding `job_id`.

---

### ❌ 15. Candidates from DB Are Not Loaded
**What's missing:** Candidates scanned in previous sessions are never loaded from Supabase `resume_scans`. Every page load starts with an empty list. The database is being written to but never read from in the UI.

---

### ❌ 16. No Loading / Error State for the Recruiter File Processing
**What's missing:** If a file fails to process (network error, API down), the failure is silently swallowed with a `console.error`. There is no user-facing error state or retry mechanism.

---

### ❌ 17. Groq API Key is Hardcoded in Source Code
In `src/llm_engine.py`:
```python
api_key="your_api_key_here"
```
This is a serious **security vulnerability**. The key is exposed to anyone with access to the repository. It should be moved to environment variables.

---

### ❌ 18. No Request Rate Limiting or Queue for Bulk Upload
**What's missing:** If a recruiter uploads 50 resumes simultaneously, the API fires 50 parallel LLM calls. Groq's free tier has rate limits (30 requests/min). This will fail silently after the first few.

**What's needed:** A job queue (e.g., simple asyncio queue or Celery task) to process resumes sequentially or with limited concurrency, with progress feedback to the UI.

---

### ❌ 19. No DOCX File Support (Despite Being Accepted)
The file input accepts `.docx` files but there is no DOCX parsing in `api/main.py`. The fallback reads it as plain text, which produces garbage output for `.docx` binary format.

**Fix:** Add `python-docx` library for DOCX parsing.

---

### ❌ 20. No Resume Parse Caching
The same resume uploaded twice triggers full re-processing (PDF text extraction + NER + LLM × 3 calls). There is no content-hash-based caching to skip reprocessing identical documents.

---

## 🎨 Frontend Gaps

### ❌ 21. No Progress Indicator for Multi-Resume Uploads
When processing 10 resumes, the UI just shows "Processing..." for the entire batch. Users have no idea which resume is being processed, how many are done, or whether it's stuck.

**What's needed:** A live progress bar showing `3/10 resumes processed`.

---

### ❌ 22. Improvement Tips Have No Category Icons or Priority Labels
The improvement tips are rendered as a flat list of text blocks. A professional tool would:
- Group them by category with icons (🔴 Skills, 🟡 Experience, 🔵 Education)
- Sort them by impact (critical → important → minor)
- Show which tips have the highest ATS score impact

---

### ❌ 23. Candidate Dashboard: No Resume Score History
A candidate who analyzes their resume 3 times (after each round of edits) sees only the latest result. There is no score history or trend chart showing improvement over time.

---

### ❌ 24. Recruiter Candidate Table: No "View Full Report" / Detail Panel
Clicking on a candidate in the table does nothing. A professional tool would open a detail panel/drawer showing:
- Full improvement tips for that candidate
- Complete skills breakdown
- Resume PDF inline viewer
- Comparison vs. the job requirements

---

### ❌ 25. No Mobile Responsiveness
Both the recruiter and candidate dashboards use a fixed sidebar + main layout that breaks on small screens. The `h-screen flex` containers overflow on mobile.

---

### ❌ 26. Login Page Has a Dev-Only Warning Visible to All Users
The yellow "Local Testing Alert" banner about Supabase email confirmation is hard-coded into the production login UI. This should be removed or conditionally shown based on `NODE_ENV`.

---

### ❌ 27. No "Forgot Password" / Email Verification Flow
There is no password reset link on the login page, and no handling of the Supabase email verification callback URL. Users who forget their password have no self-service recovery path.

---

### ❌ 28. Recruiter Job Posts Are Hardcoded as Dummy Data Initially
```tsx
const [jobs, setJobs] = useState<any[]>([
  { id: '1', title: 'Senior Frontend Developer', description: '...' },
  { id: '2', title: 'Backend Engineer (Python)', description: '...' }
])
```
New recruiters sign up and immediately see fake jobs that don't belong to them.

---

## 📊 Summary Priority Table

| # | Gap | Layer | Severity |
|---|-----|-------|----------|
| 13 | `proxy.ts` not recognized as middleware — no auth guard | Backend | 🔴 Critical |
| 17 | Groq API Key hardcoded in source | Backend | 🔴 Critical |
| 1 | No resume section segmentation | NLP | 🔴 Critical |
| 2 | No years-of-experience calculation | NLP | 🔴 Critical |
| 14 | Jobs not persisted to Supabase | Backend | 🔴 Critical |
| 15 | Candidates not loaded from DB on refresh | Backend | 🔴 Critical |
| 19 | DOCX files produce garbage output | Backend | 🔴 Critical |
| 4 | No formatting/structure quality check | NLP | 🟠 High |
| 7 | No keyword-by-keyword JD matching | NLP | 🟠 High |
| 8 | No STAR/XYZ bullet format detection | NLP | 🟠 High |
| 11 | Score blending formula is arbitrary | NLP | 🟠 High |
| 18 | No rate limiting for bulk upload | Backend | 🟠 High |
| 21 | No progress indicator for bulk upload | Frontend | 🟠 High |
| 24 | No candidate detail panel | Frontend | 🟠 High |
| 3 | No education tier/degree recognition | NLP | 🟡 Medium |
| 5 | Skill DB missing modern categories | NLP | 🟡 Medium |
| 6 | No context-aware skill validation | NLP | 🟡 Medium |
| 9 | No certifications extraction | NLP | 🟡 Medium |
| 10 | No domain-adaptive score weighting | NLP | 🟡 Medium |
| 12 | No comparative candidate benchmarking | NLP | 🟡 Medium |
| 16 | Silent error handling in bulk upload | Backend | 🟡 Medium |
| 20 | No resume parse caching | Backend | 🟡 Medium |
| 22 | Improvement tips lack priority/grouping | Frontend | 🟡 Medium |
| 23 | No score history for candidates | Frontend | 🟡 Medium |
| 25 | No mobile responsiveness | Frontend | 🟡 Medium |
| 26 | Dev warning banner in production login | Frontend | 🟡 Medium |
| 27 | No forgot password flow | Frontend | 🟡 Medium |
| 28 | Hardcoded dummy jobs on sign-up | Frontend | 🟡 Medium |
