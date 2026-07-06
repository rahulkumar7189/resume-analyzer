"""
generate_llm_dataset.py (formerly download_extra_datasets.py)
--------------------------
Downloads resume datasets from Hugging Face and formats them into
ChatML JSONL pairs required for Llama-3/Mistral instruction-tuning.

Format:
{"messages": [
    {"role": "system", "content": "You are an expert ATS AI. Extract skills..."},
    {"role": "user", "content": "Resume Text Here"},
    {"role": "assistant", "content": "{\"skills\": [\"Python\", \"React\"]}"}
]}

Output:
------
  data/processed/finetune_dataset.jsonl
"""

import json
import urllib.request
import urllib.parse
import time
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
OUT_JSONL = Path("data/processed/finetune_dataset.jsonl")

# ── Dataset 1: datasetmaster/resumes via HF Datasets API ──────────────────────
HF_DATASET   = "datasetmaster/resumes"
HF_BATCH     = 100
HF_DELAY     = 1.5

SYSTEM_PROMPT = "You are a professional ATS AI. Extract all technical skills, soft skills, and certifications from the provided resume text. Respond ONLY in valid JSON format: {\"skills\": [\"skill1\", \"skill2\"]}"

def hf_fetch_rows(offset: int, length: int) -> list:
    """Fetch a batch of rows from HF datasets-server."""
    params = urllib.parse.urlencode({
        "dataset": HF_DATASET,
        "config": "default",
        "split": "train",
        "offset": offset,
        "length": length,
    })
    url = f"https://datasets-server.huggingface.co/rows?{params}"
    
    retries = 3
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read()).get("rows", [])
        except Exception as e:
            if attempt < retries - 1:
                wait = 5 * (2 ** attempt)
                print(f"  [retry {attempt+1}] {e} -- waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  [!] Gave up fetching offset={offset}: {e}")
                return []
    return []

def hf_get_total_rows() -> int:
    """Get total row count from the HF splits endpoint."""
    try:
        params = urllib.parse.urlencode({"dataset": HF_DATASET})
        url    = f"https://datasets-server.huggingface.co/splits?{params}"
        req    = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            
        for split in data.get("splits", []):
            if split.get("split") == "train" and split.get("config") == "default":
                return split.get("num_rows", 0)
    except Exception as e:
        print(f"  [!] Error fetching total rows: {e}")
    return 0

def create_jsonl_dataset():
    """Download HF datasets and compile them into a JSONL format."""
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[*] Fetching HF dataset: {HF_DATASET} for LLM Fine-Tuning")
    total_rows = hf_get_total_rows()
    print(f"    Estimated rows: {total_rows:,}")

    doc_count = 0

    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for offset in range(0, total_rows, HF_BATCH):
            rows = hf_fetch_rows(offset, HF_BATCH)
            if not rows:
                break

            for row_wrapper in rows:
                row = row_wrapper.get("row", {})

                text = (
                    row.get("resume_text") or
                    row.get("text") or
                    row.get("resume") or
                    row.get("content") or
                    row.get("Resume_str") or
                    ""
                )
                if not text or not text.strip():
                    continue

                text = text.strip()[:8000]

                skills_raw = (
                    row.get("skills") or
                    row.get("skill_list") or
                    row.get("technical_skills") or
                    []
                )

                skills_list = []
                if isinstance(skills_raw, list):
                    skills_list = [s.strip() for s in skills_raw if isinstance(s, str) and s.strip()]
                elif isinstance(skills_raw, str) and skills_raw.strip():
                    skills_list = [s.strip() for s in skills_raw.split(",") if s.strip()]

                if not skills_list:
                    continue

                # Create the ChatML JSON object
                chat_ml_obj = {
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": text},
                        {"role": "assistant", "content": json.dumps({"skills": skills_list})}
                    ]
                }
                
                f.write(json.dumps(chat_ml_obj) + "\n")
                doc_count += 1

            time.sleep(HF_DELAY)

            if offset % 500 == 0:
                print(f"    {offset:>5,} / {total_rows:,} rows fetched | docs={doc_count:,}")

    print(f"\n[*] Finished! Successfully wrote {doc_count:,} fine-tuning examples to {OUT_JSONL}")

if __name__ == "__main__":
    create_jsonl_dataset()
