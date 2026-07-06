# 🎯 Resume ATS Analyzer — Intelligent Backend Pipeline

A modular, production-ready backend system that analyzes any PDF resume against a job description and returns a **structured, weighted ATS score** plus **actionable improvement tips** — all powered by a custom-trained spaCy NER model and the Groq LLM API.

---

## 📐 Architecture Overview

```
PDF Resume
    │
    ▼
┌─────────────────────────┐
│   main.py  (CLI entry)  │
└────────────┬────────────┘
             │
     ┌───────┴────────┐
     │                │
     ▼                ▼
┌──────────┐   ┌─────────────────────────────────────────────┐
│ PyPDF2   │   │            src/llm_engine.py                 │
│ Text     │   │                                              │
│ Extract  │   │  5-dimension weighted scoring via Groq LLM  │
└──────────┘   │  (skills_match · experience · education ·   │
               │   projects · presentation)                   │
               └─────────────────────────────────────────────┘
                            │
                            ▼
                   ResumeFeedback (JSON)
                   ├── overall_score  (0–10, weighted)
                   └── improvement_tips[]
                         ├── category
                         ├── issue_found
                         └── actionable_fix
```

The spaCy NER pipeline (`src/extractor.py`) can optionally pre-extract skills from the resume to pass as context to the LLM, further improving scoring accuracy.

---

## ✨ Features

| Feature | Implementation |
|---------|---------------|
| **PDF text extraction** | `PyPDF2` — lightweight, works on Windows without poppler |
| **Skill extraction (NER)** | Custom spaCy model trained on 3,650 annotated resumes (`SKILL` label) |
| **Weighted ATS scoring** | 5 independent dimensions scored by LLM, aggregated in Python |
| **Bias-free scoring** | Scores computed mathematically — LLM cannot "anchor" to a fixed number |
| **Structured output** | Pydantic-validated `ResumeFeedback` JSON — no hallucination leakage |
| **Job description input** | Paste inline (`--job`) or load from a `.txt` file (`--job-file`) |
| **Robust error handling** | Graceful fallback on LLM parse failures — never crashes |

---

## 🗂️ Project Structure

```
NLP/
├── main.py                    # CLI entry point — run this to analyze a resume
├── config.cfg                 # spaCy training configuration (CPU/GPU ready)
├── fix_labels.py              # One-time label normalization utility
├── requirements.txt           # Python dependencies
├── job.txt                    # (Optional) Paste your job description here
│
├── src/
│   ├── data_pipeline.py       # Downloads & converts Hugging Face dataset → .spacy
│   ├── extractor.py           # PDF text extraction + spaCy NER skill extractor
│   ├── scorer.py              # TF-IDF cosine similarity ATS scorer
│   └── llm_engine.py          # Groq LLM client — weighted multi-dimension scoring
│
├── data/
│   ├── raw/                   # Raw JSON annotation files from Hugging Face
│   └── processed/
│       ├── train.spacy        # Original corpus (from data_pipeline.py)
│       └── train_fixed.spacy  # Label-normalized corpus (use this for training)
│
└── models/
    ├── model-best/            # Best checkpoint (use this for inference)
    └── model-last/            # Final checkpoint
```

---

## ⚙️ Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
pip install PyPDF2
```

> **Note for GPU training**: install the correct cupy version for your CUDA version:
> ```bash
> pip install cupy-cuda12x   # CUDA 12.x (e.g. CUDA 12.2)
> pip install cupy-cuda13x   # CUDA 13.x (e.g. CUDA 13.0)
> ```

### 2. Verify your setup

```bash
python -c "import spacy, PyPDF2, openai, pydantic; print('All dependencies OK')"
```

---

## 🏗️ Training the NER Model (One-time setup)

> **Skip this section if `models/model-best/` already exists.**

### Step 1 — Build the dataset

Downloads ~3,650 annotated resumes from Hugging Face and converts them to spaCy binary format:

```bash
python src/data_pipeline.py
```

This creates `data/processed/train.spacy`.

### Step 2 — Fix labels (critical)

The raw dataset labels entities as `SKILL: Python`, `SKILL: Docker`, etc. (the entity text embedded in the label name). This produces 8,000+ unique label types, which is impossible for NER to learn. This script normalizes all labels to a single `SKILL` class:

```bash
python fix_labels.py
```

This creates `data/processed/train_fixed.spacy` — the correct training file.

### Step 3 — Train

#### GPU (recommended — RTX 4060 / any NVIDIA GPU)

```bash
python -m spacy train config.cfg \
  --output ./models \
  --paths.train ./data/processed/train_fixed.spacy \
  --paths.dev   ./data/processed/train_fixed.spacy \
  --gpu-id 0
```

#### CPU (slower, works on any machine)

```bash
python -m spacy train config.cfg \
  --output ./models \
  --paths.train ./data/processed/train_fixed.spacy \
  --paths.dev   ./data/processed/train_fixed.spacy \
  --gpu-id -1
```

**Expected training output** (rows appear within ~2 minutes):

```
E    #       LOSS TOK2VEC  LOSS NER  ENTS_F  ENTS_P  ENTS_R  SCORE
---  ------  ------------  --------  ------  ------  ------  ------
  0     50       5.23      345.67   12.45   10.20   15.80    0.12
  0    100       4.01      289.34   34.12   32.10   36.80    0.34
  0    150       3.44      210.11   52.45   50.30   55.10    0.52
```

Training completes in ~15–30 min on GPU, ~2–3 hours on CPU with the current config.

---

## 🚀 Usage

### Basic (no job description)

```bash
python main.py path/to/resume.pdf
```

> ⚠️ Without a job description, scoring is less accurate — the LLM evaluates the resume in isolation.

---

### With a job description (recommended)

#### Option A — Paste text inline

```bash
python main.py resume.pdf --job "Senior Python Backend Engineer with 3+ years FastAPI, PostgreSQL, Docker, AWS..."
```

#### Option B — Load from a file (best for long LinkedIn/Naukri JDs)

1. Copy the full job description from LinkedIn or Naukri
2. Paste it into `job.txt` (already in the project root)
3. Run:

```bash
python main.py resume.pdf --job-file job.txt
```

---

### With manually specified missing skills

```bash
python main.py resume.pdf --job-file job.txt --missing "Docker,Kubernetes,AWS SageMaker"
```

---

## 📤 Output Format

The script prints a JSON object to stdout:

```json
{
  "overall_score": 7.4,
  "improvement_tips": [
    {
      "category": "skills_match",
      "issue_found": "No mention of FastAPI or REST API design experience",
      "actionable_fix": "Add a dedicated Skills section listing FastAPI, REST API design, and any relevant frameworks"
    },
    {
      "category": "experience",
      "issue_found": "Only 1 internship listed — role requires 5 years of backend experience",
      "actionable_fix": "Expand each experience entry with specific technical achievements and metrics"
    },
    {
      "category": "presentation",
      "issue_found": "No quantified achievements (e.g. 'reduced latency by 30%')",
      "actionable_fix": "Add numbers and impact to each bullet point to demonstrate measurable results"
    }
  ]
}
```

### Scoring dimensions & weights

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| `skills_match` | **30%** | Overlap between resume skills and job requirements |
| `experience` | **25%** | Depth, relevance, and years of work experience |
| `projects` | **20%** | Quality and relevance of projects to the target role |
| `education` | **15%** | Degree relevance and institution prestige |
| `presentation` | **10%** | Formatting, clarity, and quantified achievements |

> The LLM scores each dimension independently (0–10) and the final `overall_score` is computed as a **weighted average in Python** — this prevents the model from always outputting the same score.

---

## 🧠 How Scoring Works (Technical Detail)

```
LLM scores 5 dimensions → Python computes weighted average → overall_score
```

1. The Groq LLM (`llama-3.3-70b-versatile`, `temperature=0.6`) is asked to score 5 **independent** dimensions against the provided job description.
2. The raw dimension scores are returned as JSON (`dimension_scores` key).
3. Python applies the weights table above and computes `round(weighted_sum, 1)`.
4. This design eliminates LLM score anchoring (where the model always returns ~8.5).

---

## 🔧 Key Configuration (`config.cfg`)

| Setting | Value | Purpose |
|---------|-------|---------|
| `max_length` | `512` | Truncates long resumes — prevents GPU hanging on 1000-token docs |
| `batcher.start` | `8` | Small initial batch — first training row appears in ~2 min |
| `batcher.stop` | `64` | Max batch size — keeps CPU/GPU memory usage low |
| `eval_frequency` | `50` | Logs every 50 steps — gives frequent feedback |
| `max_steps` | `1500` | Completes in reasonable time on CPU |
| `patience` | `200` | Stops early if ENTS_F doesn't improve for 200 evals |

---

## 🛠️ Troubleshooting

### Training header appears but no rows print

**Cause**: Documents were too long (avg 533 tokens) and/or labels were broken (8,472 unique labels).

**Fix**: Ensure you ran `python fix_labels.py` and are using `train_fixed.spacy`. Check `config.cfg` has `max_length = 512`.

### `ENTS_F` score stays at 0.0

**Cause**: Using the original `train.spacy` with broken labels (`SKILL: Python` instead of `SKILL`).

**Fix**: Run `python fix_labels.py` and use `train_fixed.spacy`.

### GPU shows 0% utilization during training

**Cause**: cupy/CUDA version mismatch or deadlock during GPU memory allocation.

**Fix**: Use `--gpu-id -1` (CPU mode) or reinstall the correct cupy version:
```bash
pip install cupy-cuda12x  # or cupy-cuda13x depending on your CUDA version
```

### `Error during LLM call: name '_default_feedback' is not defined`

Already fixed in current `src/llm_engine.py`. Pull the latest code.

### Score always shows 8.2 or 8.5

**Cause**: Old single-score prompt. Now fixed — the LLM scores 5 dimensions independently.

**Fix**: Ensure you have the latest `src/llm_engine.py` with `_WEIGHTS` and `_SYSTEM_PROMPT`.

### `2 validation errors for ResumeFeedback`

**Cause**: Old LLM response format — Groq was wrapping output in a `{"feedback": {...}}` key.

**Fix**: Current `llm_engine.py` unwraps this automatically.

---

## 📦 Dependencies

```
spacy              # NER model training and inference
huggingface_hub    # Dataset download
pdfplumber         # PDF text extraction (alternative extractor)
PyPDF2             # PDF text extraction (main.py)
scikit-learn       # TF-IDF cosine similarity scorer
openai             # Groq API client (OpenAI-compatible)
pydantic           # Structured output validation
```

Install all:
```bash
pip install -r requirements.txt
pip install PyPDF2
```

---

## 🔑 API Key

The Groq API key is configured in `src/llm_engine.py`. To use your own key, replace the value in:

```python
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="your_groq_api_key_here",
)
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).

---

## 📊 Dataset

- **Source**: [`Mehyaar/Annotated_NER_PDF_Resumes`](https://huggingface.co/datasets/Mehyaar/Annotated_NER_PDF_Resumes) on Hugging Face
- **Size**: 3,650 annotated resume documents
- **Original labels**: 8,472 unique (`SKILL: <word>` format) → normalized to 1 label: `SKILL`
- **After normalization**: 226,923 `SKILL` entities across 3,650 documents
- **Avg document length**: 533 tokens (truncated to 512 during training)
