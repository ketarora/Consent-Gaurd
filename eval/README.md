# Consent Guard evaluation instructions

This folder contains a small reproducible evaluation script and instructions to compute dataset statistics and run the deterministic prefilter checks locally.

How to reproduce

1. Create and activate a Python virtualenv (you can reuse backend/requirements.txt):

```bash
python -m venv venv
source venv/bin/activate    # or venv\\Scripts\\activate on Windows
pip install -r backend/requirements.txt
```

2. Run the evaluation script (it reads the top-level consent_guard_dataset.json):

```bash
python eval/run_eval.py --input consent_guard_dataset.json --out eval/results.json --clean
```

The script will:
- compute per-category counts
- compute flagged vs clean counts
- optionally produce a cleaned dataset at eval/consent_guard_dataset_cleaned.json (if --clean)
- write summary to the output JSON file

Notes
- This script is local-only and does not call any external LLM APIs by default.
- If you want the script to call the LLM classifier for a sample, set up your provider keys and use the appropriate flags (see the top of the script).
