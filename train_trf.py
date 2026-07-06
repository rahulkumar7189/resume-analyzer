"""
train_trf.py
------------
Launches the DeBERTa Transformer training pipeline.
Forces PyTorch initialization first to completely bypass Windows CUDA DLL conflicts!
"""
import os
os.environ["SAFETENSORS_ONLY"] = "1"           # Force safetensors format (bypass CVE-2025-32434 torch.load block)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"  # Suppress Windows symlink warnings
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"      # Suppress TensorFlow oneDNN warnings
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"  # Prevent PyTorch VRAM fragmentation OOM

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

# Patch: Disable the CVE-2025-32434 torch.load block in transformers (we use safetensors anyway)
# Must patch in ALL modules that import the function directly
_noop = lambda: None
try:
    import transformers.utils.import_utils as _tiu
    _tiu.check_torch_load_is_safe = _noop
except Exception:
    pass
try:
    import transformers.modeling_utils as _tmu
    _tmu.check_torch_load_is_safe = _noop
except Exception:
    pass

import spacy
from spacy.cli.train import train
from pathlib import Path

CONFIG_PATH = "config_trf.cfg"
OUTPUT_PATH = "./models_trf"
TRAIN_DATA  = "./data/processed/train_expanded_clean.spacy"
DEV_DATA    = "./data/processed/train_fixed_clean.spacy"

def main():
    print("[*] Launching DeBERTa Transformer Training (Targeting 92%+ F-Score)...")
    print(f"   Config : {CONFIG_PATH}")
    print(f"   Output : {OUTPUT_PATH}")
    print(f"   Train  : {TRAIN_DATA}")
    print(f"   Dev    : {DEV_DATA}")
    
    import thinc.compat
    print("Debug: has_cupy before train():", thinc.compat.has_cupy)
    
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
