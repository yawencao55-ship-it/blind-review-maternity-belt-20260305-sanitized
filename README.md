# Anonymous Review Package

This repository contains source code, analysis scripts, and model-generated datasets for anonymous peer review.

## Structure

- `src/`: Python source code and dependencies file.
- `data/`: input datasets and parameter tables used by the computational workflow.
- `results/`: generated numeric outputs (CSV/JSON) used for analysis and figure production.

## Quick Start

```bash
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r src/requirements.txt
python src/advanced_fea_analysis.py
python src/advanced_visualization.py
```

## Reproducibility Note

All datasets included here are either literature-derived parameter tables, publicly available data extracts, or model-generated outputs used in the manuscript analyses.
