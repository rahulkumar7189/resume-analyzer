"""Quick test: can spaCy train even 1 step on a tiny subset of data?"""
import spacy
from spacy.tokens import DocBin
import time

print("Loading data...")
nlp = spacy.blank("en")
db = DocBin().from_disk("./data/processed/train.spacy")
docs = list(db.get_docs(nlp.vocab))
print(f"Total docs: {len(docs)}")

# Take only the 10 shortest docs
docs_sorted = sorted(docs, key=len)
tiny = docs_sorted[:10]
print(f"Using {len(tiny)} shortest docs, lengths: {[len(d) for d in tiny]}")

# Save tiny subset
tiny_db = DocBin()
for d in tiny:
    tiny_db.add(d)
tiny_db.to_disk("./tiny_train.spacy")
print("Saved tiny_train.spacy")

# Now try training with spacy CLI equivalent
print("\nAttempting training...")
from spacy.cli.train import train
from pathlib import Path
import tempfile, shutil

# Use a minimal config
config_text = """
[paths]
train = "./tiny_train.spacy"
dev = "./tiny_train.spacy"

[system]
gpu_allocator = null
seed = 0

[nlp]
lang = "en"
pipeline = ["ner"]
batch_size = 100

[training]
dev_corpus = "corpora.dev"
train_corpus = "corpora.train"
seed = ${system.seed}
gpu_allocator = ${system.gpu_allocator}
dropout = 0.1
patience = 50
max_epochs = 0
max_steps = 10
eval_frequency = 5

[training.optimizer]
@optimizers = "Adam.v1"

[training.batcher]
@batchers = "spacy.batch_by_words.v1"
discard_oversize = false
tolerance = 0.2

[training.batcher.size]
@schedules = "compounding.v1"
start = 100
stop = 1000
compound = 1.001

[training.logger]
@loggers = "spacy.ConsoleLogger.v1"
progress_bar = true

[training.score_weights]
ents_f = 1.0
ents_p = 0.0
ents_r = 0.0

[corpora.train]
@readers = "spacy.Corpus.v1"
path = ${paths.train}
max_length = 0
gold_preproc = false
limit = 0
augmenter = null

[corpora.dev]
@readers = "spacy.Corpus.v1"
path = ${paths.dev}
max_length = 0
gold_preproc = false
limit = 0
augmenter = null

[components.ner]
factory = "ner"

[components.ner.model]
@architectures = "spacy.TransitionBasedParser.v2"
state_type = "ner"
extra_state_tokens = false
hidden_width = 64
maxout_pieces = 2
use_upper = true

[components.ner.model.tok2vec]
@architectures = "spacy.HashEmbedCNN.v2"
pretrained_vectors = null
width = 96
depth = 4
embed_size = 2000
window_size = 1
maxout_pieces = 3
subword_features = true
"""

with open("tiny_config.cfg", "w") as f:
    f.write(config_text)

print(f"Config written. Starting training at {time.strftime('%H:%M:%S')}...")
start = time.time()
try:
    train("tiny_config.cfg", Path("./tiny_models"), use_gpu=0, overrides={})
except Exception as e:
    print(f"ERROR: {e}")
elapsed = time.time() - start
print(f"Finished in {elapsed:.1f}s")
