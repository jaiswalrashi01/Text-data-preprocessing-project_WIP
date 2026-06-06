"""
Step 1 — Tidy up the columns and remove rows that have no headline.

In plain terms:
  - The raw dataset has lots of columns (the article text, the headline,
    the web link, a date, etc.). We only need some of them, so we throw
    away the ones we won't use.
  - Some rows have no headline at all (it's blank or missing). A news
    story with no title isn't useful to us, so we delete those rows.

(We keep the "description" and "domain" columns for now. They get used
later during the boilerplate step, and are removed there instead.)
"""

from __future__ import annotations

import logging

import pandas as pd

# A "logger" is just a tidy way to print progress messages.
logger = logging.getLogger(__name__)


def drop_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Remove the listed columns from the table and return the smaller table.

    Think of the data as a spreadsheet. This deletes whole columns we don't
    need (for example the web link or the date).
    """
    # Only try to remove columns that are actually there — if one is already
    # gone, we just skip it instead of crashing.
    present = [c for c in columns if c in df.columns]
    return df.drop(columns=present)


def drop_empty_titles(df: pd.DataFrame, title_col: str = "title") -> tuple[pd.DataFrame, int]:
    """Delete rows whose headline is missing or blank, and renumber the rows.

    Returns the cleaned table AND a count of how many rows were removed.
    """
    # Find rows where the title is empty. We treat three cases as "empty":
    #   1) the title is missing entirely (NaN)
    #   2) the title is an empty piece of text ("")
    #   3) the title is only spaces ("   ")
    # fillna("") turns a missing title into an empty piece of text, so all
    # three cases become the same simple check: "is it blank after trimming?"
    blank = df[title_col].fillna("").astype(str).str.strip() == ""

    # Count how many blank-title rows we found.
    n_removed = int(blank.sum())

    # Keep only the rows that are NOT blank (the "~" means "not"), then
    # renumber the rows 0, 1, 2, ... so there are no gaps left behind.
    clean = df.loc[~blank].reset_index(drop=True)

    return clean, n_removed


def run(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Do the whole of Step 1, using the settings from config.yaml."""
    # Read the choices from the config file instead of typing them here,
    # so they're easy to change in one place later.
    title_col = cfg["dataset"]["title_col"]
    drop_initial = cfg["columns"]["drop_initial"]

    before = len(df)

    # 1) Remove the columns we don't need.
    df = drop_columns(df, drop_initial)

    # 2) Remove rows that have no headline.
    df, n_titles = drop_empty_titles(df, title_col=title_col)

    # Print a short progress note so we can see what happened.
    logger.info("Step 1 | dropped columns: %s", drop_initial)
    logger.info("Step 1 | removed %d empty-title rows (%d -> %d rows)",
                n_titles, before, len(df))
    return df
