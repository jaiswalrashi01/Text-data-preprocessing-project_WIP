"""
Step (late) — Find near-duplicate / boilerplate articles with MinHash + LSH.

Plain-English idea
------------------
A lot of news articles are near-copies of each other (syndicated stories,
template pages, "subscribe to read" stubs). We want to find those so we can
review and remove them. Comparing every article to every other article would
take forever, so we use two tricks:

  1. SHINGLES — chop each article into overlapping chunks of N words. Two
     articles that share most of their chunks are probably near-copies.
  2. MinHash + LSH — instead of storing all the chunks, we make a small
     "fingerprint" of each article (MinHash) and drop it into a lookup system
     (LSH) that can instantly tell us "have I already seen an article very
     similar to this one?" — without checking all the others one by one.

Articles that cluster together get counted. Clusters that show up in at least
THRESHOLD articles are written to data/audits/ as candidates for YOU to
review (this step finds them; a human decides what to remove).

This reads the data from a CSV in small chunks so the whole dataset never has
to sit in memory at once — that's what prevents the out-of-memory crashes.
"""

from __future__ import annotations

import gc
import logging
from pathlib import Path

import pandas as pd
from datasketch import MinHash, MinHashLSH

logger = logging.getLogger(__name__)

TEXT_COL = "text_clean"


def get_shingles(text: str, n: int) -> set[str]:
    """Chop text into overlapping chunks of n words.

    Example (n=3): "the quick brown fox" -> {"the quick brown", "quick brown fox"}.
    Returns an empty set if the text is shorter than n words.
    """
    words = str(text).lower().split()
    if len(words) < n:
        return set()
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def discover_near_duplicates(input_csv: Path | str, cfg: dict) -> pd.DataFrame:
    """Scan the cleaned text and list articles that are near-identical.

    Writes the candidate list to data/audits/ (as both .csv for you to
    eyeball and .parquet for the next step) and also returns it.
    """
    # Read the settings from config instead of hardcoding them.
    mh = cfg["boilerplate"]["minhash"]
    n_size = mh["n_size"]
    similarity = mh["similarity"]
    num_perm = mh["num_permutations"]
    chunk_size = mh["chunk_size"]
    threshold = mh["threshold"]

    audits = cfg["paths"]["audits"]
    audits.mkdir(parents=True, exist_ok=True)
    out_csv = audits / "discovered_boilerplate.csv"
    out_parquet = audits / "discovered_boilerplate.parquet"

    # LSH is the lookup system that groups similar fingerprints into "buckets".
    lsh = MinHashLSH(threshold=similarity, num_perm=num_perm)
    bucket_text: dict[str, str] = {}    # bucket -> the first article text seen for it
    bucket_count: dict[str, int] = {}   # bucket -> how many articles landed in it
    next_bucket = 0

    # Read the file a few thousand rows at a time so memory stays low.
    for chunk in pd.read_csv(input_csv, usecols=[TEXT_COL], chunksize=chunk_size):
        for text in chunk[TEXT_COL].dropna():
            shingles = get_shingles(text, n_size)
            if not shingles:
                continue

            # Build this article's small fingerprint from its chunks.
            fingerprint = MinHash(num_perm=num_perm)
            for s in shingles:
                fingerprint.update(s.encode("utf8"))

            # Ask LSH: have we already seen a very similar article?
            matches = lsh.query(fingerprint)
            if matches:
                # Yes -> add this one to the existing group's count.
                bucket_count[matches[0]] += 1
            else:
                # No -> start a new group with this article as its example.
                key = f"k{next_bucket}"
                lsh.insert(key, fingerprint)
                bucket_text[key] = text
                bucket_count[key] = 1
                next_bucket += 1

        gc.collect()  # release memory after each chunk

    # Keep only the groups that appeared in enough articles to be worth review.
    rows = [
        {"phrase": bucket_text[k], "count": c}
        for k, c in bucket_count.items()
        if c >= threshold
    ]
    if rows:
        results = (pd.DataFrame(rows)
                   .sort_values("count", ascending=False)
                   .reset_index(drop=True))
    else:
        # Nothing crossed the threshold — return an empty table with the
        # right columns instead of crashing.
        results = pd.DataFrame(columns=["phrase", "count"])

    results.to_parquet(out_parquet, index=False)
    results.to_csv(out_csv, index=False)

    logger.info("Boilerplate discovery | n=%d, similarity=%.2f, threshold=%d "
                "-> %d candidate groups", n_size, similarity, threshold, len(results))
    logger.info("Boilerplate discovery | wrote %s and %s", out_csv.name, out_parquet.name)
    return results


def apply_removal(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Remove rows based on YOUR hand-labeled decisions.

    Reads the review file from data/audits/ (the one with the 'action'
    column you filled in). For each labeled article text:
      - action 0  -> remove EVERY row whose text matches it (pure junk)
      - action 1  -> keep the FIRST copy, remove the other copies (duplicates)

    The matching is on the whole cleaned article text, so this removes whole
    rows (articles) — it never cuts into the articles you keep.
    """
    audits = cfg["paths"]["audits"]
    audit_file = audits / cfg["boilerplate"]["audit_file"]

    # This step can't run without your hand-labeled file. Say so plainly.
    if not audit_file.exists():
        raise FileNotFoundError(
            f"Boilerplate audit file not found: {audit_file}\n"
            "This step needs the hand-labeled review file (with an 'action' "
            "column). Put it in data/audits/ — see data/audits/README.md."
        )

    audit = pd.read_excel(audit_file)
    missing = {"phrase", "action"} - set(audit.columns)
    if missing:
        raise ValueError(f"audit file is missing required column(s): {missing}")

    # Split the labeled phrases into the two groups.
    remove_all = set(audit.loc[audit["action"] == 0, "phrase"].unique())
    keep_first = set(audit.loc[audit["action"] == 1, "phrase"].unique())

    df = df.copy()
    before = len(df)

    # action 0: drop every row whose text matches a "remove all" phrase.
    mask_remove_all = df[TEXT_COL].isin(remove_all)
    n_action_0 = int(mask_remove_all.sum())
    df = df.loc[~mask_remove_all]

    # action 1: among the "keep first" phrases, drop only the repeat copies
    # (a row counts as a repeat if the same text appeared earlier in the table).
    in_keep_first = df[TEXT_COL].isin(keep_first)
    is_repeat = df.duplicated(subset=[TEXT_COL], keep="first")
    mask_action_1 = in_keep_first & is_repeat
    n_action_1 = int(mask_action_1.sum())
    df = df.loc[~mask_action_1].reset_index(drop=True)

    logger.info("Boilerplate removal | action-0 removed %d rows; "
                "action-1 removed %d duplicate copies (%d -> %d rows)",
                n_action_0, n_action_1, before, len(df))
    return df
