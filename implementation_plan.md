# Intelligent ATS Analyzer Backend Pipeline

This plan outlines the creation of a highly modular, decoupled backend architecture for an Intelligent ATS Analyzer. The architecture focuses on deterministic data extraction, mathematical scoring, and constrained LLM generation. 

## User Review Required

> [!IMPORTANT]
> Since you are on a Windows machine (`d:\NLP`), I am planning to create `train.sh` as you requested, but please note you will need a bash emulator (like Git Bash or WSL) to run `.sh` scripts. Alternatively, I can provide a `train.bat` or `train.ps1` script if you prefer native Windows execution. 
> 
> Also, please ensure you have an OpenAI API key set in your environment variables (`OPENAI_API_KEY`) before running the final pipeline.

## Proposed Changes

### Data Pipeline & Training Automation
This component handles downloading the dataset, resolving overlapping annotations, converting to spaCy format, and providing the training script.

#### [NEW] src/data_pipeline.py
- Uses `huggingface_hub` to download `ResumesJsonAnnotated.zip` and extracts it to `data/raw/`.
- Parses the individual JSON files, filtering out overlapping entity highlights using `spacy.util.filter_spans()`.
- Saves the cleaned dataset as a DocBin to `data/processed/train.spacy`.

#### [NEW] train.sh
- A bash script automating the spaCy configuration and training commands:
  - `python -m spacy init config config.cfg --lang en --pipeline ner --optimize efficiency --force`
  - `python -m spacy train config.cfg --output ./models --paths.train ./data/processed/train.spacy --paths.dev ./data/processed/train.spacy`

---

### Intelligent ATS Analyzer Backend
The core application decoupled into three specific functions: extraction, scoring, and feedback generation.

#### [NEW] src/extractor.py
- Implements `extract_text(pdf_path)` using `pdfplumber` for high-accuracy text extraction from columns and layouts.
- Implements `extract_skills_locally(text)` which loads `./models/model-best` and returns a unique list of technical skills found.

#### [NEW] src/scorer.py
- Implements `calculate_ats_match(extracted_resume_skills, job_description_text)`.
- Uses `scikit-learn`'s `TfidfVectorizer` (with `stop_words='english'`) to vectorize the input.
- Computes mathematical overlap using `cosine_similarity`.
- Returns the percentage score (0-100) and calculates `missing_skills` based on set logic between Job Skills and Resume Skills.

#### [NEW] src/llm_engine.py
- Uses `openai` python SDK and Pydantic for structured generation.
- Defines `ResumeTip` and `ResumeFeedback` Pydantic models.
- Implements `generate_strict_feedback(resume_text, job_description, missing_skills)`.
- Strictly sets `temperature=0.1` and uses `client.beta.chat.completions.parse` with the `gpt-4o` model to eliminate hallucinations.

#### [NEW] main.py
- The entry point script at the root level.
- Sequentially runs a sample PDF through the pipeline: `extractor.py` -> `scorer.py` -> `llm_engine.py`.
- Outputs the deterministic skills extracted, the objective mathematical score, and structured tips returned by the LLM.

#### [NEW] requirements.txt
- Lists all required dependencies (`spacy`, `huggingface_hub`, `pdfplumber`, `scikit-learn`, `openai`, `pydantic`).

#### [NEW] README.md
- Clear instructions on how to install dependencies, run the data pipeline, train the model, and execute the final testing script.

## Verification Plan

### Automated Tests
- Running the `data_pipeline.py` and verifying `train.spacy` is successfully generated without overlap errors.

### Manual Verification
- Execution of the `train.sh` script to verify spaCy loss calculation and `model-best` generation.
- Running `main.py` with a dummy PDF to test the `extractor`, `scorer`, and `llm_engine` flow, ensuring the response matches the strictly defined Pydantic JSON schema.
