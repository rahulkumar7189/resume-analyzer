import os
import json
import zipfile
from huggingface_hub import hf_hub_download
import spacy
from spacy.tokens import DocBin
from spacy.util import filter_spans

def main():
    print("Downloading dataset...")
    # Pull the exact zip file from the Hugging Face repository
    zip_path = hf_hub_download(
        repo_id="Mehyaar/Annotated_NER_PDF_Resumes", 
        repo_type="dataset", 
        filename="ResumesJsonAnnotated.zip"
    )

    print("Extracting files...")
    extract_dir = "./data/raw"
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
      
    print("Converting to spaCy format...")
    nlp = spacy.blank("en") # Blank model to process the text
    db = DocBin() # Container for our binary data

    json_folder = os.path.join(extract_dir, "ResumesJsonAnnotated")
    if not os.path.exists(json_folder):
        json_folder = extract_dir

    valid_files = [f for f in os.listdir(json_folder) if f.endswith('.json')]

    for filename in valid_files:
        filepath = os.path.join(json_folder, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            text = data.get("text", "")
            text = "".join(c if not (0xD800 <= ord(c) <= 0xDFFF) else " " for c in text)
            annotations = data.get("annotations", [])
            
            doc = nlp.make_doc(text)
            ents = []
            
            for annot in annotations:
                if isinstance(annot, list) and len(annot) >= 3:
                    start_char, end_char, label = annot[0], annot[1], annot[2]
                elif isinstance(annot, dict):
                    start_char, end_char, label = annot.get("start"), annot.get("end"), annot.get("label")
                else:
                    continue
                
                span = doc.char_span(
                    start_char, 
                    end_char, 
                    label=label, 
                    alignment_mode="contract"
                )
                if span is not None:
                    ents.append(span)
            
            # Automatically removes messy overlaps
            doc.ents = filter_spans(ents)
            db.add(doc)

    # Save the compiled dataset to your machine
    output_dir = "./data/processed"
    os.makedirs(output_dir, exist_ok=True)
    db.to_disk(os.path.join(output_dir, "train.spacy"))
    print(f"Successfully processed {len(db)} resumes into data/processed/train.spacy!")

if __name__ == "__main__":
    main()
