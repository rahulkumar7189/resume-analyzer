"""
parser.py
---------
Professional resume section segmentation and structured data extraction.

Provides:
  - Section-based segmentation (HEADER, CONTACT, SUMMARY, EXPERIENCE,
    EDUCATION, PROJECTS, SKILLS, CERTIFICATIONS, AWARDS, LANGUAGES, VOLUNTEER)
  - Date range parsing and total years-of-experience computation
  - Education degree type, field, institution, GPA extraction
  - Certifications extraction (known certs + section-level fallback)
  - Contact info (name, email, phone, LinkedIn, GitHub, portfolio)

Usage:
    from src.parser import parse_resume, ParsedResume
    parsed = parse_resume(resume_text)
    print(parsed.total_experience_months // 12, "years experience")
    print(parsed.education)
    print(parsed.certifications)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# ── Section heading pattern registry ─────────────────────────────────────────

_SECTION_PATTERNS: dict[str, list[str]] = {
    "CONTACT": [
        r"\b(contact(\s+information)?)\b", r"\b(personal(\s+information)?)\b",
        r"\b(personal(\s+details)?)\b", r"\b(personal(\s+data)?)\b",
    ],
    "SUMMARY": [
        r"\b((professional\s+)?summary)\b", r"\b(objective)\b", r"\b(profile)\b",
        r"\b(about(\s+me)?)\b", r"\b(career\s+(objective|goal|profile|summary))\b",
        r"\b(professional\s+profile)\b", r"\b(executive\s+summary)\b",
    ],
    "EXPERIENCE": [
        r"\b((work|professional|employment|job)?\s*(experience|history|background))\b",
        r"\b(professional\s+experience)\b", r"\b(career\s+history)\b",
        r"\b(internship(s)?(\s+experience)?)\b", r"\b(work\s+history)\b",
        r"\b(employment(\s+history)?)\b",
    ],
    "EDUCATION": [
        r"\b(education(al)?(\s+background)?)\b", r"\b(academic(\s+background)?)\b",
        r"\b(qualifications?)\b", r"\b(degrees?)\b", r"\b(academic\s+credentials?)\b",
    ],
    "SKILLS": [
        r"\b((technical\s+)?skills?)\b", r"\b(core\s+competenc(y|ies))\b",
        r"\b(technologies(\s+&\s+tools?)?)\b", r"\b(tech(nical)?\s+stack)\b",
        r"\b(key\s+skills?)\b", r"\b(proficienc(y|ies))\b", r"\b(expertise)\b",
        r"\b(tools?\s+&\s+technologies?)\b", r"\b(programming\s+languages?)\b",
        r"\b(technical\s+proficienc(y|ies))\b",
    ],
    "PROJECTS": [
        r"projects?(\s+&\s+publications?)?", r"personal\s+projects?",
        r"side\s+projects?", r"open[\s\-]source(\s+projects?)?",
        r"portfolio", r"academic\s+projects?", r"key\s+projects?",
    ],
    "CERTIFICATIONS": [
        r"certifications?", r"certificates?", r"credentials?",
        r"professional\s+certifications?",
        r"licenses?\s*(and|&)?\s*certifications?",
        r"courses?\s*(and|&)?\s*certifications?",
        r"continuing\s+education",
    ],
    "AWARDS": [
        r"awards?(\s+(and|&)\s+honors?)?", r"honors?",
        r"achievements?", r"accomplishments?", r"recognition",
        r"awards?\s+and\s+achievements?",
    ],
    "PUBLICATIONS": [
        r"publications?", r"papers?", r"research(\s+papers?)?",
        r"articles?", r"conferences?",
    ],
    "LANGUAGES": [
        r"languages?(\s+known)?", r"spoken\s+languages?",
        r"language\s+proficienc(y|ies)",
    ],
    "VOLUNTEER": [
        r"volunteer(ing|s)?(\s+experience)?",
        r"community\s+(service|involvement|engagement)",
        r"extra[\s\-]?curricular",
    ],
    "INTERESTS": [
        r"interests?", r"hobbies(\s+and\s+interests?)?",
        r"activities", r"personal\s+interests?",
    ],
    "REFERENCES": [
        r"references?(\s+available)?",
    ],
}


def _build_section_detector() -> list[tuple[str, re.Pattern]]:
    """Compile all section heading patterns into regex objects."""
    compiled = []
    for section_name, patterns in _SECTION_PATTERNS.items():
        for p in patterns:
            compiled.append((
                section_name,
                re.compile(
                    r'^[\s\-\*\•\=\_\#]*(' + p + r')[\s\:\-\*\•\=\_\#]*$',
                    re.IGNORECASE,
                )
            ))
    return compiled


_SECTION_DETECTOR = _build_section_detector()


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ContactInfo:
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    leetcode: str = ""
    portfolio: str = ""
    location: str = ""


@dataclass
class DateRange:
    start_year: Optional[int] = None
    start_month: Optional[int] = None
    end_year: Optional[int] = None
    end_month: Optional[int] = None
    is_current: bool = False

    def duration_months(self) -> int:
        """Compute the total number of months spanned by this date range."""
        if self.start_year is None:
            return 0
        start = date(self.start_year, self.start_month or 1, 1)
        if self.is_current:
            end = date.today()
        elif self.end_year:
            end = date(self.end_year, self.end_month or 12, 1)
        else:
            return 0
        return max(0, (end.year - start.year) * 12 + (end.month - start.month))


@dataclass
class ExperienceEntry:
    title: str = ""
    company: str = ""
    date_range: DateRange = field(default_factory=DateRange)
    bullets: list[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class EducationEntry:
    degree: str = ""          # full raw degree string
    degree_type: str = ""     # "Bachelor" | "Master" | "PhD" | "MBA" | "Diploma" | "Associate"
    field: str = ""           # field of study
    institution: str = ""
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None


@dataclass
class ParsedResume:
    sections: dict[str, str] = field(default_factory=dict)
    contact: ContactInfo = field(default_factory=ContactInfo)
    experience: list[ExperienceEntry] = field(default_factory=list)
    education: list[EducationEntry] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    total_experience_months: int = 0
    raw_text: str = ""

    # Convenience properties
    @property
    def experience_years(self) -> float:
        return round(self.total_experience_months / 12, 1)

    @property
    def highest_degree(self) -> str:
        order = ["PhD", "Master", "MBA", "Bachelor", "Associate", "Diploma", "High School"]
        for d in order:
            if any(e.degree_type == d for e in self.education):
                return d
        return ""


# ── Date parsing ──────────────────────────────────────────────────────────────

_MONTH_MAP: dict[str, int] = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

_DATE_RANGE_RE = re.compile(
    r'(?P<sm>[A-Za-z]{3,9}\.?)?\s*(?P<sy>20[0-2]\d|19[8-9]\d)'
    r'\s*(?:–|—|-{1,2}|to)\s*'
    r'(?:(?P<em>[A-Za-z]{3,9}\.?)?\s*(?P<ey>20[0-2]\d|19[8-9]\d)'
    r'|(?P<cur>present|current|now|ongoing|till\s+date|today))',
    re.IGNORECASE,
)

_SINGLE_YEAR_RE = re.compile(r'\b(20[0-2]\d|19[8-9]\d)\b')


def _parse_date_range(text: str) -> Optional[DateRange]:
    """Extract a DateRange from a line of text. Returns None if no date range found."""
    m = _DATE_RANGE_RE.search(text)
    if not m:
        return None

    dr = DateRange()
    sy = m.group("sy")
    sm = m.group("sm")
    if sy:
        dr.start_year = int(sy)
    if sm:
        dr.start_month = _MONTH_MAP.get(sm.lower().rstrip('.'), 1)

    if m.group("cur"):
        dr.is_current = True
    else:
        ey = m.group("ey")
        em = m.group("em")
        if ey:
            dr.end_year = int(ey)
        if em:
            dr.end_month = _MONTH_MAP.get(em.lower().rstrip('.'), 12)

    return dr


# ── Education extraction ──────────────────────────────────────────────────────

_DEGREE_TIERS: list[tuple[re.Pattern, str]] = [
    (re.compile(r'\bPh\.?D\.?\b|\bDoctor(?:ate|al)?\b', re.IGNORECASE), "PhD"),
    (re.compile(r'\bM\.?Tech\.?\b|\bM\.?E\.?\b|\bM\.?Eng\.?\b', re.IGNORECASE), "Master"),
    (re.compile(r'\bM\.?S\.?(?:\s|$|,)|\bM\.?Sc\.?\b', re.IGNORECASE), "Master"),
    (re.compile(r'\bMaster(?:s)?(?:\s+of|\s+in|\'s)?\b', re.IGNORECASE), "Master"),
    (re.compile(r'\bM\.?B\.?A\.?\b', re.IGNORECASE), "MBA"),
    (re.compile(r'\bB\.?Tech\.?\b|\bB\.?E\.?\b|\bB\.?Eng\.?\b', re.IGNORECASE), "Bachelor"),
    (re.compile(r'\bB\.?Sc\.?\b|\bB\.?S\.?(?:\s|$|,)', re.IGNORECASE), "Bachelor"),
    (re.compile(r'\bBachelor(?:s)?(?:\s+of|\s+in|\'s)?\b', re.IGNORECASE), "Bachelor"),
    (re.compile(r'\bB\.?A\.?(?:\s|$|,)', re.IGNORECASE), "Bachelor"),
    (re.compile(r'\bAssociate(?:s)?\b', re.IGNORECASE), "Associate"),
    (re.compile(r'\bDiploma\b', re.IGNORECASE), "Diploma"),
    (re.compile(r'\bHigh\s+School\b|\bSecondary\b|\b10\+2\b|\bHSC\b|\bSSC\b', re.IGNORECASE), "High School"),
]

_FIELD_KEYWORDS: list[str] = [
    "Computer Science", "Software Engineering", "Information Technology",
    "Electrical Engineering", "Electronics", "Mechanical Engineering",
    "Civil Engineering", "Chemical Engineering", "Biomedical", "Biotechnology",
    "Data Science", "Artificial Intelligence", "Machine Learning",
    "Mathematics", "Statistics", "Physics", "Chemistry",
    "Business Administration", "Finance", "Economics",
    "Computer Engineering", "Information Systems", "Cybersecurity",
    "Cognitive Science", "Computational Linguistics",
]

_GPA_RE = re.compile(r'\bGPA[\s:]*(\d+\.?\d*)\s*/?\s*(\d+\.?\d*)?', re.IGNORECASE)


def _extract_education(section_text: str) -> list[EducationEntry]:
    """Parse education section into structured EducationEntry objects."""
    entries: list[EducationEntry] = []
    lines = [l.strip() for l in section_text.splitlines() if l.strip()]

    i = 0
    while i < len(lines):
        line = lines[i]
        entry = EducationEntry()

        # Detect degree type in this line
        for pattern, dtype in _DEGREE_TIERS:
            if pattern.search(line):
                entry.degree_type = dtype
                entry.degree = line
                break

        if not entry.degree_type:
            i += 1
            continue

        # Look ahead 2 lines for institution / field / GPA
        look_ahead = " ".join(lines[i: min(i + 3, len(lines))])

        for field_kw in _FIELD_KEYWORDS:
            if field_kw.lower() in look_ahead.lower():
                entry.field = field_kw
                break

        # Institution: next line that isn't a degree line itself
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            is_degree_line = any(p.search(next_line) for p, _ in _DEGREE_TIERS)
            if not is_degree_line and len(next_line) > 3:
                entry.institution = next_line

        # Graduation year
        yr_m = _SINGLE_YEAR_RE.search(look_ahead)
        if yr_m:
            entry.graduation_year = int(yr_m.group(0))

        # GPA
        gpa_m = _GPA_RE.search(look_ahead)
        if gpa_m:
            try:
                entry.gpa = float(gpa_m.group(1))
            except ValueError:
                pass

        entries.append(entry)
        i += 1

    return entries


# ── Certifications extraction ─────────────────────────────────────────────────

_KNOWN_CERTS: list[str] = [
    # AWS
    "AWS Certified Solutions Architect", "AWS Certified Developer",
    "AWS Certified SysOps", "AWS Certified DevOps", "AWS Certified Data Analytics",
    "AWS Certified Machine Learning", "AWS Certified Security",
    "AWS Certified Database", "AWS Certified Advanced Networking",
    "AWS SAA", "AWS SAP", "AWS DVA", "AWS SOA", "AWS MLS", "AWS DEA",
    # GCP
    "Google Cloud Professional", "Google Cloud Associate",
    "GCP Professional Data Engineer", "GCP Professional Cloud Architect",
    "GCP Associate Cloud Engineer", "Google Professional",
    # Azure
    "Azure AZ-900", "Azure AZ-104", "Azure AZ-204", "Azure AZ-305",
    "Azure DP-100", "Azure AI-900", "Azure AZ-400", "Azure AZ-500",
    "Microsoft Certified", "Azure Administrator", "Azure Developer",
    "Azure Data Engineer", "Azure AI Engineer",
    # Kubernetes / Docker
    "CKA", "CKAD", "CKS", "Certified Kubernetes Administrator",
    "Certified Kubernetes Application Developer",
    "Docker Certified Associate", "HashiCorp Certified", "Terraform Associate",
    # Project Management
    "PMP", "CAPM", "Prince2", "CSM", "PSM", "Certified Scrum Master",
    "Professional Scrum Master", "SAFe", "Agile Certified Practitioner",
    # Security
    "CEH", "OSCP", "CISSP", "CISA", "CISM", "CompTIA Security+",
    "CompTIA Network+", "CompTIA A+", "CompTIA CySA+",
    "CCNA", "CCNP", "CCIE",
    # Data / Analytics
    "Tableau Desktop Specialist", "Tableau Server Certified",
    "Power BI Data Analyst", "Google Analytics",
    "Salesforce Certified", "Databricks Certified",
    # AI / ML
    "TensorFlow Developer Certificate", "Deep Learning Specialization",
    "Machine Learning Specialization", "AI For Everyone",
    "IBM Data Science", "IBM AI Engineering",
    "Coursera Machine Learning", "Hugging Face",
    # General
    "Oracle Certified", "Red Hat Certified", "RHCE", "RHCSA",
    "Linux Foundation Certified", "LFCS", "LFCE",
    "ITIL", "Six Sigma", "Green Belt", "Black Belt",
    "PMI-ACP", "TOGAF",
]

_CERT_RE = re.compile(
    r'(?:' + '|'.join(re.escape(c) for c in sorted(_KNOWN_CERTS, key=len, reverse=True)) + r')',
    re.IGNORECASE,
)

_BULLET_RE = re.compile(r'^[\s]*[•\-–—*>▸▹○◦◆▪]\s*(.+)', re.MULTILINE)


def _extract_certifications(cert_section_text: str, full_text: str = "") -> list[str]:
    """
    Extract certifications from the CERTIFICATIONS section (preferred) and
    fall back to scanning the entire resume for known cert names.
    """
    found: list[str] = []
    seen: set[str] = set()

    # 1. Search for known cert names in the certifications section
    search_text = cert_section_text if cert_section_text else full_text
    for m in _CERT_RE.finditer(search_text):
        cert = m.group(0).strip()
        key = cert.lower()
        if key not in seen:
            found.append(cert)
            seen.add(key)

    # 2. If we have a CERTIFICATIONS section but found nothing via regex,
    #    grab every bullet/line as a raw certification entry
    if not found and cert_section_text:
        for line in cert_section_text.splitlines():
            line = line.strip("•-–—*> \t▸▹○◦◆▪")
            if 5 < len(line) < 150:
                key = line.lower()
                if key not in seen:
                    found.append(line)
                    seen.add(key)

    return found


# ── Contact info extraction ───────────────────────────────────────────────────

_EMAIL_RE = re.compile(r'[\w.+\-]+@[\w.\-]+\.\w{2,}')
# Phone regex: require at least 7 pure digit chars to avoid matching year ranges
_PHONE_RE = re.compile(r'(?<![\d])(\+?[\d][\d\s\-().]{7,14}[\d])(?![\d])')
_PURE_DIGITS_RE = re.compile(r'\d')
_LINKEDIN_RE = re.compile(r'(?:linkedin\.com/in/|linkedin[:\s]+)([\w\-]+)', re.IGNORECASE)
_GITHUB_RE = re.compile(r'(?:github\.com/|github[:\s]+)([\w\-]+)', re.IGNORECASE)
_LEETCODE_RE = re.compile(r'(?:leetcode\.com/|leetcode[:\s]+)([\w\-]+)', re.IGNORECASE)
_PORTFOLIO_RE = re.compile(r'https?://(?!github|linkedin|leetcode)([\w.\-/]+)', re.IGNORECASE)


def _extract_contact(top_text: str) -> ContactInfo:
    """Extract contact details from the top portion of the resume."""
    c = ContactInfo()

    em = _EMAIL_RE.search(top_text)
    if em:
        c.email = em.group(0)

    # Only treat a match as a phone number if it has >= 7 digit chars
    # (prevents year ranges like '2020 2023' being mistaken for phones)
    for ph_m in _PHONE_RE.finditer(top_text):
        candidate = ph_m.group(0).strip()
        if len(_PURE_DIGITS_RE.findall(candidate)) >= 7:
            c.phone = candidate
            break

    li = _LINKEDIN_RE.search(top_text)
    if li:
        c.linkedin = "https://linkedin.com/in/" + li.group(1)

    gh = _GITHUB_RE.search(top_text)
    if gh:
        c.github = "https://github.com/" + gh.group(1)

    lc = _LEETCODE_RE.search(top_text)
    if lc:
        c.leetcode = "https://leetcode.com/" + lc.group(1)

    port = _PORTFOLIO_RE.search(top_text)
    if port:
        c.portfolio = port.group(0)

    # Candidate name — usually the first short non-email, non-phone line
    for line in top_text.splitlines()[:8]:
        line = line.strip()
        if not line:
            continue
        if '@' in line or re.search(r'\d{4,}', line):
            continue
        words = line.split()
        if 1 <= len(words) <= 5 and len(line) < 60:
            c.name = line
            break

    return c


# ── Section segmentation ──────────────────────────────────────────────────────

def segment_sections(text: str) -> dict[str, str]:
    """
    Split resume text into labeled sections.
    Unrecognized content at the top becomes the HEADER section.

    Returns:
        Dict mapping section_name (str) -> section_text (str).
    """
    lines = text.splitlines()
    sections: dict[str, str] = {}
    current_section = "HEADER"
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        matched = None

        for section_name, pattern in _SECTION_DETECTOR:
            if pattern.match(stripped):
                matched = section_name
                break

        if matched:
            # Save accumulated lines under current section
            content = "\n".join(current_lines).strip()
            if content:
                sections[current_section] = content
            current_section = matched
            current_lines = []
        else:
            current_lines.append(line)

    # Flush last section
    content = "\n".join(current_lines).strip()
    if content:
        sections[current_section] = content

    return sections


# ── Experience section parser ─────────────────────────────────────────────────

_BULLET_LINE_RE = re.compile(r'^[\s]*[•\-–—*>▸▹○◦◆▪]\s+')
_TITLE_INDICATOR_RE = re.compile(
    r'\b(engineer|developer|analyst|scientist|manager|lead|intern|architect|'
    r'designer|consultant|director|head|specialist|associate|coordinator|'
    r'administrator|officer|executive|president|vice|senior|junior|principal|'
    r'staff|fellow|researcher|professor|lecturer|teacher|agent)\b',
    re.IGNORECASE,
)


def _parse_experience_section(section_text: str) -> list[ExperienceEntry]:
    """Parse the EXPERIENCE section into a list of ExperienceEntry objects."""
    entries: list[ExperienceEntry] = []
    lines = section_text.splitlines()

    current: Optional[ExperienceEntry] = None
    bullets: list[str] = []

    def _flush():
        nonlocal current, bullets
        if current is not None:
            current.bullets = bullets[:]
            entries.append(current)
        current = None
        bullets = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        date_range = _parse_date_range(stripped)

        if date_range and date_range.start_year:
            # New experience block
            _flush()
            current = ExperienceEntry(date_range=date_range)

            # Try to extract title from the same line (before the year)
            try:
                year_str = str(date_range.start_year)
                if year_str in stripped:
                    before_year = stripped[:stripped.index(year_str)].strip()
                    before_year = re.sub(r'[\-–—|,]+$', '', before_year).strip()
                    if before_year and len(before_year) < 80:
                        current.title = before_year
            except (ValueError, TypeError):
                pass

        elif _BULLET_LINE_RE.match(stripped):
            bullet_text = _BULLET_LINE_RE.sub('', stripped)
            bullets.append(bullet_text)

        elif current is not None:
            # Could be company name or continuation of title
            if not current.company and not _TITLE_INDICATOR_RE.search(stripped):
                current.company = stripped
            elif not current.title and _TITLE_INDICATOR_RE.search(stripped):
                current.title = stripped

    _flush()
    return entries


# ── Main public API ───────────────────────────────────────────────────────────

def parse_resume(text: str) -> ParsedResume:
    """
    Parse a resume text string into a structured ParsedResume object.

    Args:
        text: Plain text content of the resume.

    Returns:
        ParsedResume with sections, contact, experience, education,
        certifications, and computed experience years.
    """
    result = ParsedResume(raw_text=text)

    # 1. Segment into sections
    result.sections = segment_sections(text)

    # 2. Contact info from header + first 600 chars
    header_text = result.sections.get("HEADER", "")
    top_snippet = header_text + "\n" + text[:600]
    result.contact = _extract_contact(top_snippet)

    # 3. Parse experience entries
    exp_text = result.sections.get("EXPERIENCE", "")
    if exp_text:
        result.experience = _parse_experience_section(exp_text)

    # 4. Total experience months (deduplicated — overlapping roles count once)
    result.total_experience_months = sum(
        e.date_range.duration_months() for e in result.experience
    )

    # 5. Education
    edu_text = result.sections.get("EDUCATION", "")
    if edu_text:
        result.education = _extract_education(edu_text)

    # 6. Certifications
    cert_text = result.sections.get("CERTIFICATIONS", "")
    awards_text = result.sections.get("AWARDS", "")
    result.certifications = _extract_certifications(cert_text, text)

    # Also scan awards section for cert keywords
    if awards_text:
        extra = _extract_certifications(awards_text)
        seen = {c.lower() for c in result.certifications}
        result.certifications += [c for c in extra if c.lower() not in seen]

    return result


# ── Educational & Experience Normalization ────────────────────────────────────

DEGREE_TIERS = {
    "high school": 0,
    "diploma": 1,
    "polytechnic": 1,
    "associate": 1,
    "btech": 2,
    "be": 2,
    "bachelor": 2,
    "bsc": 2,
    "ba": 2,
    "mtech": 3,
    "me": 3,
    "master": 3,
    "msc": 3,
    "mba": 3,
    "ma": 3,
    "phd": 4,
    "doctorate": 4
}

def extract_jd_required_degree(jd_text: str) -> str:
    """
    Heuristically extract the minimum required degree from the JD text.
    Returns the key found in DEGREE_TIERS, or empty string if none found.
    """
    jd_clean = jd_text.lower().replace(".", "")
    found_tiers = []
    
    # We want the minimum degree mentioned that isn't just a stray word
    # For a robust approach, we check words in context, but a simple 
    # string match works for our tiers list if we match exact bounds.
    for key in DEGREE_TIERS.keys():
        if re.search(r'\b' + re.escape(key) + r'\b', jd_clean):
            found_tiers.append((key, DEGREE_TIERS[key]))
            
    if not found_tiers:
        return ""
        
    # Sort by tier to find the minimum requirement
    found_tiers.sort(key=lambda x: x[1])
    return found_tiers[0][0]

def evaluate_education_fit(candidate_degree: str, required_degree: str) -> float:
    """
    Normalizes and compares academic credentials to prevent penalizing over-qualification.
    Returns 1.0 if candidate meets or exceeds requirements, fractional otherwise.
    """
    if not required_degree:
        return 1.0 # If no degree is required, they fit
        
    # Standardize string tokens
    cand_clean = candidate_degree.lower().replace(".", "").strip()
    req_clean = required_degree.lower().replace(".", "").strip()
    
    # Extract corresponding tier values
    cand_tier = next((val for key, val in DEGREE_TIERS.items() if key in cand_clean), -1)
    req_tier = next((val for key, val in DEGREE_TIERS.items() if key in req_clean), -1)
    
    # If we couldn't parse the requirement, default to pass to avoid false negatives
    if req_tier == -1:
        return 1.0
        
    # If candidate degree is unrecognized but requirement is, we don't know, default 0.5
    if cand_tier == -1:
        return 0.5
    
    # If the candidate possesses a higher or identical qualification level, grant full score
    if cand_tier >= req_tier and req_tier >= 0:
        return 1.0
    
    # Fallback to standard fractional logic if tiers are unmatched or lower
    return 0.0 if req_tier > cand_tier else 0.5
