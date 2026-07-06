# Intelligent ATS Analyzer Backend

I have successfully scaffolded the backend architecture for the Intelligent ATS Analyzer, fully aligned with your specifications for a decoupled, high-accuracy pipeline.

## Deliverables

All code has been created under `d:\NLP`:

1. **[requirements.txt](file:///d:/NLP/requirements.txt)**: Python dependencies including `spacy`, `huggingface_hub`, `pdfplumber`, `scikit-learn`, `openai`, and `pydantic`.
2. **[src/data_pipeline.py](file:///d:/NLP/src/data_pipeline.py)**: The script that downloads `ResumesJsonAnnotated.zip` directly from Hugging Face, bypasses the broken API viewer, unpacks it into `data/raw/`, and correctly leverages `spacy.util.filter_spans` to fix the overlapping labels issue before generating `train.spacy`.
3. **[train.sh](file:///d:/NLP/train.sh)**: Automates generating `config.cfg` and running the training routine to produce `./models/model-best`. 
4. **[src/extractor.py](file:///d:/NLP/src/extractor.py)**: Takes a PDF path, extracts the text using `pdfplumber` for superior layout retention, and extracts skills deterministically using the custom spaCy NER model.
5. **[src/scorer.py](file:///d:/NLP/src/scorer.py)**: Performs mathematical overlap logic via scikit-learn's `TfidfVectorizer` and `cosine_similarity`, calculating the ATS Match Score and isolating `missing_skills`.
6. **[src/llm_engine.py](file:///d:/NLP/src/llm_engine.py)**: Implements strict logic using `gpt-4o` with `temperature=0.1` and Pydantic models for structured, hallucination-free JSON responses.
7. **[main.py](file:///d:/NLP/main.py)**: Integrates the flow natively in a command line script for easy testing.
8. **[README.md](file:///d:/NLP/README.md)**: Documentation on setting up the environment and executing the sequence.

## Next Steps

> [!TIP]
> **Getting Started**
> To run this locally, open up your terminal (e.g. Git Bash) and execute the following:
> 
> ```bash
> pip install -r requirements.txt
> python src/data_pipeline.py
> bash train.sh
> ```
> 
> Once the model finishes training, export your OpenAI API key and test your application with:
> ```bash
> python main.py <path_to_your_sample_resume_pdf>
> ```

Feel free to inspect the generated code files in your workspace! If you encounter any issues executing the `train.sh` script on Windows or need assistance integrating this backend with your Streamlit frontend, just let me know.

