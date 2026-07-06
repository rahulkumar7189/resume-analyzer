import re
import sys

with open('llm_engine_backup.py', 'rb') as f:
    text = f.read().decode('utf-16le').replace('\r\n', '\n').replace('\r', '')

# 1. Update ResumeFeedback
text = re.sub(
    r'class ResumeFeedback\(BaseModel\):\n    overall_score: float\n    improvement_tips: list\[ResumeTip\]\n    domain: str = "software_engineering"',
    'class ResumeFeedback(BaseModel):\n    overall_score: float\n    improvement_tips: list[ResumeTip]\n    domain: str = "software_engineering"\n    hr_red_flags: list[str] = []',
    text,
    count=1
)

# 2. Update JSON structure in _SYSTEM_PROMPT
text = re.sub(
    r'      "star_missing":   <true if this bullet/entry lacks a quantified Result>\n    }\n  ]\n}',
    '      "star_missing":   <true if this bullet/entry lacks a quantified Result>\n    }\n  ],\n  "hr_red_flags": [\n    <list of strings detailing critical HR red flags like unintentional age bias, vague wording, repetitive clichés, tone mismatches>\n  ]\n}',
    text,
    count=1
)

# 3. Update Rules in _SYSTEM_PROMPT
text = re.sub(
    r'- impact="high" if fixing this tip would boost ATS score by 10\+ points\.',
    '- impact="high" if fixing this tip would boost ATS score by 10+ points.\n- Identify "HR Red Flags" such as obvious grammar errors, extreme exaggerations, over-used buzzwords (e.g. "synergy"), or discriminatory/biased language.',
    text,
    count=1
)

# 4. Update ResumeFeedback instantiation
text = re.sub(
    r'    feedback = ResumeFeedback\(\n        overall_score=overall_score,\n        improvement_tips=tips,\n        domain=domain,\n    \)',
    '    feedback = ResumeFeedback(\n        overall_score=overall_score,\n        improvement_tips=tips,\n        domain=domain,\n        hr_red_flags=data.get("hr_red_flags", []),\n    )',
    text,
    count=1
)

with open('src/llm_engine.py', 'wb') as f:
    f.write(text.encode('utf-8'))

print("File patched successfully!")
