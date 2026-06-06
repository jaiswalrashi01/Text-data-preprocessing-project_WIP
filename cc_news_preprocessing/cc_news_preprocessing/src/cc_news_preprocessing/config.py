"""Central configuration loader.

Single source of truth for paths and parameters. Nothing else in the
codebase should hardcode a path or a magic number -- they all come from
config/config.yaml through this module. This is what replaces every
hardcoded /content/drive/MyDrive/... path from the original notebook.

Usage
-----
    from cc_news_preprocessing.config import load_config
    cfg = load_config()
    raw_dir = cfg["paths"]["raw"]          # a pathlib.Path, already resolved
    n_size  = cfg["boilerplate"]["minhash"]["n_size"]
"""

from __future__ import annotations

from pathlib import Path

import yaml

# Project root = three levels up from this file:
#   <root>/src/cc_news_preprocessing/config.py  -> parents[2] == <root>
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


def load_config(config_path: Path | str = CONFIG_PATH) -> dict:
    """Load config.yaml and resolve all data paths to absolute pathlib.Paths.

    Callers never build a path by hand; they read fully-resolved Paths from
    cfg["paths"]. base_dir may be relative (resolved against the project
    root) or absolute (e.g. a mounted Drive path) -- both work.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    p = cfg["paths"]
    base = (PROJECT_ROOT / p["base_dir"]).resolve()  # absolute base_dir stays as-is
    cfg["paths"]["base"] = base
    cfg["paths"]["raw"] = base / p["raw_subdir"]
    cfg["paths"]["interim"] = base / p["interim_subdir"]
    cfg["paths"]["processed"] = base / p["processed_subdir"]
    cfg["paths"]["audits"] = base / p["audits_subdir"]
    return cfg


def ensure_dirs(cfg: dict) -> None:
    """Create the data directories if they don't exist (safe to call repeatedly)."""
    for key in ("raw", "interim", "processed", "audits"):
        cfg["paths"][key].mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    # Quick sanity check: `python -m cc_news_preprocessing.config`
    cfg = load_config()
    print("Project root:", PROJECT_ROOT)
    print("Resolved data paths:")
    for k in ("base", "raw", "interim", "processed", "audits"):
        print(f"  {k:10s}: {cfg['paths'][k]}")
