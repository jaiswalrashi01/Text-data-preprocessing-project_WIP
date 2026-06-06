"""
Step 3 — Clean up the text of each article (and each headline).

In plain terms: news text scraped from the web is messy. It has web
addresses, email addresses, stray line breaks, accented characters, and
inconsistent spacing. This takes one piece of text and tidies all of that,
returning a clean version. We run it on both the article body and the
headline, creating two new columns: `text_clean` and `title_clean`.

The original article text is left untouched — we only ADD the cleaned
columns, so nothing is lost and we can always compare before/after.
"""

from __future__ import annotations

import logging
import re
import unicodedata

import pandas as pd

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Take one messy string and return a tidied version."""
    # If it isn't text (e.g. a missing value), hand it back unchanged.
    if not isinstance(text, str):
        return text

    # 1. Strip accents: "résumé" -> "resume".
    #    NOTE / decision point: the second line below also removes EVERY
    #    non-English character (not just accents) -- smart quotes, dashes,
    #    and any foreign script get deleted here. This is the aggressive
    #    behaviour we discussed; kept as-is from the original run, flagged
    #    so it can be revisited deliberately rather than by accident.
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("utf-8", "ignore")

    # 2. Remove leftover line-break artifacts from scraping.
    #    ("/n" here is a literal slash-n that shows up in scraped text,
    #     not a real newline; kept from the original.)
    text = text.replace("/n", "").replace("\n", "").replace("\\n", "")

    # 3. Remove web addresses (http://..., https://..., www....).
    text = re.sub(r"https?://\S+|www\.\S+", "", text)

    # 4. Remove email addresses.
    text = re.sub(r"[A-Za-z0-9+._-]+@[A-Za-z0-9+._-]+\.[A-Za-z0-9+_-]+", "", text)

    # 5. Make everything lowercase.
    text = text.lower()

    # 6. Fix run-together sentences: add a space after . ! ? when a new
    #    word starts immediately (e.g. "end.start" -> "end. start").
    text = re.sub(r"([.!?])(?=[a-z])", r"\1 ", text)

    # 7. Collapse repeated spaces/tabs into single spaces, trim the ends.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def run(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Add cleaned text/title columns to the table, using settings from config."""
    text_col = cfg["dataset"]["text_col"]
    title_col = cfg["dataset"]["title_col"]

    df = df.copy()  # work on a copy so the caller's table isn't modified
    df["text_clean"] = df[text_col].apply(clean_text)
    df["title_clean"] = df[title_col].apply(clean_text)

    logger.info("Step 3 | added 'text_clean' and 'title_clean' columns")
    return df
