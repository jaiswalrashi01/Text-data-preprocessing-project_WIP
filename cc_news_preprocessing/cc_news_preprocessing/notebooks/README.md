# Notebooks

This folder holds the **exploratory** work — the profiling, spot-checks, and
"figuring it out" cells. Exploration is kept here on purpose: it preserves
your reasoning without polluting the reproducible pipeline in `src/`.

## Conventions

- **Clear outputs before committing.** The original notebook carried ~2.6 MB
  of embedded cell outputs (styled DataFrames). Clearing them keeps diffs
  readable. From the command line:
  ```
  jupyter nbconvert --clear-output --inplace notebooks/*.ipynb
  ```
- Notebooks are for exploration; once a step is settled, it graduates into a
  module under `src/cc_news_preprocessing/` and gets called from
  `scripts/run_pipeline.py`.

`01_exploration.ipynb` (the cleaned version of your original notebook) will
land here.
