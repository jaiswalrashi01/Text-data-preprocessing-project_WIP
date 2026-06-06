# Audits

This folder holds the **human-made decision files** the pipeline depends on.
Unlike the rest of `data/`, the hand-labeled files here **are committed to
git**, because they cannot be regenerated automatically — they encode your
judgment calls.

## What lives here

- `discovered_boilerplate_n15.xlsx` — the n=15 boilerplate phrases with a
  hand-labeled `action` column:
  - `action = 0` → remove every row containing this phrase
  - `action = 1` → keep the first occurrence, drop the rest
  This file is a **required input** to the boilerplate removal step.

## What does NOT live here (git-ignored, regenerate instead)

- `*_blacklist*.json` — the large auto-generated sentence blacklist
- `*.parquet` — discovered-phrase tables

These are produced by the discovery code and can be rebuilt, so they are not
committed (see `.gitignore`).
