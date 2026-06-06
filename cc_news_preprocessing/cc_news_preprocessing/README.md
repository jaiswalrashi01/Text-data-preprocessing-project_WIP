# CC_NEWS Preprocessing

> **Status: 🚧 Work in progress.** Cleaning is partly complete; the corpus is
> not final. Several steps still need to be figured out (see below). Full
> reasoning and the step-by-step cleaning sequence are in
> [`reports/preprocessing_report.md`](reports/preprocessing_report.md).

Turns the raw [`vblagoje/cc_news`](https://huggingface.co/datasets/vblagoje/cc_news)
dataset into a clean, English-only news corpus for downstream **concept
modeling**.

## Pipeline stages

| # | Stage | Status | Where |
|---|-------|--------|-------|
| 1 | Acquire (one-time HuggingFace download) | ✅ done | notebook (stub: `acquire.py`) |
| 2 | Drop unused columns | ✅ done | `clean_columns.py` |
| 3 | Drop empty/missing titles | ✅ done | `clean_columns.py` |
| 4 | Deduplicate articles | ✅ done | notebook → planned separate `dedup.py` |
| 5 | Detect non-English (flag only) | 🟡 flag computed, not removed | notebook |
| 6 | Clean text | ✅ done | `text_clean.py` |
| 7 | Remove boilerplate sentences | ✅ done | notebook |
| 8 | Drop description/domain | ✅ done | notebook |
| 9 | Remove near-duplicate articles (MinHash/LSH + labels) | 🟡 mostly done | `boilerplate.py` |
| 10 | Apply non-English removal | ⬜ to do | — |
| 11 | Length filtering | ⬜ to do | — |
| 12 | Label / concept mapping | ⬜ to do | — |
| 13 | Tokenization + train/val/test split | ⬜ to do | — |

> Note: going forward, stages 4 and 6 will be **swapped** (clean text first,
> then dedup) so near-duplicates differing only in spacing/case are caught.

## Project layout

```
cc_news_preprocessing/
├── README.md                       # this file
├── requirements.txt                # dependencies (+ language-detector notes)
├── config/
│   └── config.yaml                 # all paths & parameters
├── src/cc_news_preprocessing/
│   ├── config.py                   # loads config, resolves paths
│   ├── clean_columns.py            # stages 2–3   [done]
│   ├── text_clean.py               # stage 6      [done]
│   ├── boilerplate.py              # stage 9      [done]
│   ├── acquire.py                  # stage 1      [stub]
│   └── dedup.py                    # stage 4      [stub — separate script TODO]
├── scripts/
│   └── run_pipeline.py             # entry point (wires up the done steps)
├── notebooks/
│   └── 01_exploration.ipynb        # the original exploratory work (outputs cleared)
├── reports/
│   └── preprocessing_report.md     # what was done and why (the cleaning log)
└── data/                           # git-ignored except audits/ and .gitkeep
    ├── raw/  interim/  processed/
    └── audits/                     # hand-labeled inputs (committed)
```

## Setup

```bash
pip install -r requirements.txt
```

## Configure

Edit `config/config.yaml` and set `paths.base_dir` to where your data lives.
That one edit replaces every hardcoded path — nothing points at Google Drive.

## Run

```bash
python scripts/run_pipeline.py
```

This verifies the config and prints the resolved paths. Pipeline steps are
enabled in `run_pipeline.py` as they are wired up; the implemented modules
(`clean_columns`, `text_clean`, `boilerplate`) are ready to call.

## Notes

- **Data is not committed** (raw/interim/processed are git-ignored). The corpus
  is fetched in stage 1; intermediates are regenerated.
- **Boilerplate removal is human-in-the-loop:** it needs a hand-labeled audit
  file in `data/audits/` (see that folder's README). That file is committed.
- This is a **WIP version** — work is not complete. See the report for the
  open questions and known limitations.
