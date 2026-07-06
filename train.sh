#!/bin/bash

# Exit on error
set -e

echo "Initializing spaCy configuration..."
python -m spacy init config config.cfg --lang en --pipeline ner --optimize efficiency --force

echo "Training spaCy NER model..."
python -m spacy train config.cfg --output ./models --paths.train ./data/processed/train_expanded_clean.spacy --paths.dev ./data/processed/train_fixed_clean.spacy --gpu-id 0

echo "Training complete. The best model is saved at ./models/model-best"
