# CC_NEWS Preprocessing — Report (WORK IN PROGRESS)

> **Status: work in progress.** The cleaning pipeline is partly complete. The
> steps below marked *done* have been performed and (where noted) promoted into
> reproducible scripts. The steps marked *to do* are not finished — the corpus
> is **not** final. This report records what was done and why, so the work can
> be resumed, reviewed, and trusted.

---

## 1. Goal

Turn the raw `vblagoje/cc_news` dataset (~800k news articles) into a clean,
English-only news corpus for downstream **concept modeling** (the GDCM /
CTCBM methods, which use English-only data). Cleaning aims to remove
structural web noise — navigation, footers, cookie/subscription notices,
syndicated boilerplate, near-duplicate articles — while preserving genuine
article text.

## 2. Dataset

- Source: `vblagoje/cc_news` (HuggingFace), loaded once and saved to disk.
- Columns present: title, text, description, domain, url, image_url, date.
- Columns kept for cleaning: **title** and **text**. `text` was chosen over
  `description` for richer context; url / image_url / date were dropped early;
  description / domain were dropped later, during boilerplate work.

## 3. Sequence of cleaning actions (as performed)

This is the order the steps were actually run in. Status tags show what is
done, what was computed but not applied, and what remains.

1. **Load the data** — fetch CC_NEWS, save to disk, read into a table. *(done, one-time)*
2. **Drop unused columns** — url, image_url, date. *(done — promoted to `clean_columns.py`)*
3. **Drop empty/missing titles** — blank or NaN headlines removed; index reset. *(done — `clean_columns.py`)*
4. **Deduplicate articles** — no-title-but-duplicate-text rows; stories repeating
   >40 times (keep first); stories repeating 2–40 times (keep first). *(done — not yet promoted; planned as a separate dedup script)*
5. **Detect non-English articles** — flagged with the `lingua` detector. *(flag computed; rows NOT yet removed — deliberately deferred)*
6. **Clean the text** — strip accents, URLs, emails, newline artifacts;
   lowercase; fix run-together sentences; normalize whitespace → `text_clean`,
   `title_clean`. *(done — promoted to `text_clean.py`)*
7. **Remove repeated boilerplate sentences** — sentence-level removal against a
   cross-article blacklist. *(done — see decision 5b below)*
8. **Drop description and domain columns** — no longer needed. *(done)*
9. **Find & remove near-duplicate / boilerplate articles** — MinHash + LSH over
   n-word shingles (n=20, then n=15), with hand-labeled keep/remove decisions.
   *(mostly done — promoted to `boilerplate.py`; a final exact-match pass at
   similarity 0.95 was in progress)*

**Not started (next session):** apply the non-English removal (step 5),
length filtering, label/concept-column mapping, tokenization, and the
train/validation/test split.

> **Order note for future work:** steps 4 and 6 will be **swapped** going
> forward — text cleaning *then* dedup — so that articles differing only in
> spacing or capitalization are caught as duplicates. As performed, dedup ran
> before cleaning.

## 4. Key decisions and the reasoning

**(a) Empty titles.** Rows with blank/NaN titles carry no usable signal, so
they were removed.

**(b) Language tooling.** Several detectors were tried before one worked on
Colab's Python: `fasttext` (failed to build), `pycld3` (failed to install),
and finally **`lingua`** (works — now the chosen detector). Non-English rows
are detected but **not yet removed**: inspection showed some articles begin in
another language but continue in English, so a naive "drop if foreign" rule
would discard valid content. Removal is deferred until after symbol-stripping
and cleaning, then the rule will be designed on what remains.

**(c) Deduplication.** Done in passes, keeping the first occurrence each time:
no-title-but-duplicate-text rows; stories repeating >40 times; stories
repeating 2–40 times. A final audit confirmed uniqueness on (title, text).

**(d) Text cleaning.** Accents, URLs, emails, newline artifacts removed;
lowercased; run-together sentences spaced; whitespace normalized. Commas,
periods, and apostrophes are intentionally **kept**.

**(e) Boilerplate — two distinct mechanisms.** It is important that these were
two *different* operations:
  - **Sentence-level removal** (the sentence-frequency blacklist): individual
    blacklisted sentences are snipped out of articles that are otherwise kept.
  - **Document-level removal** (MinHash + LSH): whole near-duplicate articles
    are removed (or collapsed to one copy). This never cuts into kept articles.

**Sentence-level boilerplate removal (detail).** Sentences appearing in ≥2
articles were removed from article bodies (floor = 2). A sample of the
blacklisted phrases was inspected and consistently found to be structural
boilerplate — navigation, cookie/subscription notices, footers — rather than
meaningful content; the floor was kept at 2 on that basis. The cross-article
frequency distribution at mining time is recorded below so the threshold can
be reassessed later if needed:

| Sentence appears in… | Count |
|----------------------|-------|
| 2+ articles          | 850,292 |
| 10+ articles         | 31,628 |
| 100+ articles        | 784 |
| 1,000+ articles      | 26 |

**Document-level boilerplate (detail).** MinHash fingerprints over n-word
shingles, indexed with LSH, group near-identical articles. Candidate clusters
were exported for manual review and hand-labeled with an `action` column
(0 = remove all copies; 1 = keep the first copy, remove the rest). The
discovery pass at similarity 0.85 returned near-matches rather than exact
copies for the 2-occurrence range, so a higher floor (0.95) was used for exact
duplicates — this final pass was in progress when work paused.

## 5. Known limitations / to revisit

- **Cleaning may have under-removed.** Spot-checking the output suggested some
  regex steps did not strip everything expected (regex does what is written,
  not what is intended). A dedicated "what survived the cleaning?" verification
  pass is needed before the corpus is treated as final.
- **Accent normalization is aggressive.** The accent step
  (`encode('ascii', 'ignore')`) removes *all* non-ASCII characters, not only
  accents — including smart quotes, dashes, and any foreign script. This
  overlaps with the (still undecided) non-English removal and should be made a
  deliberate choice.
- **Email regex edge case.** When an email runs directly into the next word
  with no space, the pattern can remove that following word too. Minor; affects
  only run-together text.
- **Sentence-floor of 2** is recorded above with its full distribution so a
  future reviewer can reassess how aggressive the sentence-level removal was.

## 6. Reproducibility

- All paths and parameters live in `config/config.yaml`; no hardcoded paths.
- One random seed (`random_seed`) governs all random operations.
- The document-boilerplate step is **human-in-the-loop**: it depends on a
  hand-labeled audit file in `data/audits/`, which is committed because it
  cannot be regenerated automatically.
- Heavy intermediate files (the dated `cleaned`, `cleaned2`, `cleaned3` CSVs
  from Colab) are regenerated by the pipeline and are not committed.

## 7. Code promotion status

Reproducible, tested modules in `src/cc_news_preprocessing/`:
- `clean_columns.py` — steps 2–3 (drop columns, drop empty titles)
- `text_clean.py` — step 6 (text cleaning)
- `boilerplate.py` — step 9 (near-duplicate discovery + label-driven removal)

Still in the notebook / planned as separate scripts:
- `acquire.py` — step 1 (one-time load); stub present
- `dedup.py` — step 4; stub present, to be written as a separate script
- sentence-level boilerplate (step 7), and all not-started downstream stages
