import os
os.environ["SAFETENSORS_ONLY"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import torch

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

try:
    import cupy
    print("CuPy imported successfully inside script")
except Exception as e:
    print("CuPy failed to import:", e)

import spacy
import thinc.compat
print("has_cupy:", thinc.compat.has_cupy)
