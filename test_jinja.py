from src.latex_templates import MODERN_TEMPLATE
from jinja2 import Template
import sys

print("Length:", len(MODERN_TEMPLATE))
lines = MODERN_TEMPLATE.splitlines()

for i in range(len(lines)):
    try:
        Template("\n".join(lines[:i+1]))
    except Exception as e:
        print(f"Failed at line {i+1}: {e}")
        print(f"Line content: {lines[i]}")
        sys.exit(1)
print("Success!")
