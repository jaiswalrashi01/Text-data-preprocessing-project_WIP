"""Pipeline entry point.

Runs the SETTLED preprocessing steps end to end, reading every path and
parameter from config/config.yaml. Right now it just verifies the config
wiring; each step gets uncommented as we promote it from the notebook.

Run from the project root:
    python scripts/run_pipeline.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the src/ package importable when run as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cc_news_preprocessing.config import load_config, ensure_dirs


def main() -> None:
    cfg = load_config()
    ensure_dirs(cfg)

    print("Config loaded. Resolved data paths:")
    for k in ("raw", "interim", "processed", "audits"):
        print(f"  {k:10s}: {cfg['paths'][k]}")

    # ── Pipeline steps ──
    # Implemented & tested (ready to call once a DataFrame is loaded):
    #   from cc_news_preprocessing import clean_columns, text_clean, boilerplate
    #   df = clean_columns.run(df, cfg)                         # stages 2-3  [done]
    #   df = text_clean.run(df, cfg)                            # stage 6     [done]
    #   boilerplate.discover_near_duplicates(input_csv, cfg)    # stage 9a    [done]
    #   df = boilerplate.apply_removal(df, cfg)                 # stage 9b    [done]
    #
    # Not yet wired up:
    #   acquire.load_raw(cfg)        # stage 1  [stub]
    #   dedup.run(df, cfg)           # stage 4  [separate script TODO]
    #   non-English removal, length filter, labels, tokenization, splits [TODO]


    print("\nNothing to run yet — steps are promoted one at a time.")


if __name__ == "__main__":
    main()
