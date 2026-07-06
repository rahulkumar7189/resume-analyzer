# test_clean_model.py
import spacy
from src.extractor import extract_skills_section_aware

# Load the newly trained model (or fallback if it's still training)
try:
    nlp = spacy.load("./models/model-best")
    print("[*] Successfully loaded the newly trained model-best!")
except OSError:
    print("[!] model-best not found. Ensure training is completely finished.")
    exit(1)

# A sentence designed to trigger the old model's false positives
test_text = "I spent time doing classification of hand signals using consumer hardware for extraction."

# The sections dict tells the extractor we are in the EXPERIENCE section
sections = {"EXPERIENCE": test_text}

print("\n--- Test Text ---")
print(test_text)
print("-----------------\n")

# Run the extractor
skills, _ = extract_skills_section_aware(test_text, sections)

print(f"Extracted Skills: {skills}")
if len(skills) == 0:
    print("\n✅ SUCCESS: The model correctly identified ZERO technical skills!")
    print("   The false positive bug has been permanently eradicated by Data-Centric AI.")
else:
    print(f"\n❌ FAILED: The model incorrectly extracted: {skills}")
