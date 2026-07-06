"""
train_cnn.py
------------
Launches the CNN (Tok2Vec) training pipeline.
Forces PyTorch initialization first to completely bypass Windows CUDA DLL conflicts!
"""
import cupy  # <-- CRITICAL: Force CuPy initialization first to prevent PyTorch DLL conflict!

# Patch: Force Thinc to use modern DLPack protocol (__dlpack__) instead of the buggy deprecated toDlpack()
import thinc.util
def _patched_xp2torch(xp_tensor, requires_grad=False, device=None):
    import torch
    if device is None:
        device = thinc.util.get_torch_default_device()
    # Force new DLPack protocol bypassing the buggy toDlpack()
    torch_tensor = torch.from_dlpack(xp_tensor).to(device)
    if requires_grad:
        torch_tensor.requires_grad_()
    return torch_tensor
thinc.util.xp2torch = _patched_xp2torch
import spacy
from spacy.cli.train import train
from pathlib import Path

CONFIG_PATH = "config.cfg"
OUTPUT_PATH = "./models"
TRAIN_DATA  = "./data/processed/train_expanded_clean.spacy"
DEV_DATA    = "./data/processed/train_fixed_clean.spacy"

def main():
    print("[*] Launching High-Capacity CNN Training...")
    print(f"   Config : {CONFIG_PATH}")
    print(f"   Output : {OUTPUT_PATH}")
    print(f"   Train  : {TRAIN_DATA}")
    print(f"   Dev    : {DEV_DATA}")
    
    # Run the training directly via spaCy CLI API
    train(
        config_path=Path(CONFIG_PATH),
        output_path=Path(OUTPUT_PATH),
        use_gpu=0,
        overrides={
            "paths.train": TRAIN_DATA,
            "paths.dev": DEV_DATA
        }
    )

if __name__ == "__main__":
    main()
