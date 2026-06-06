"""Step 0 — Data acquisition (ONE-TIME).

Downloads vblagoje/cc_news from HuggingFace and saves it to data/raw/.
This is a one-time fetch; the original notebook correctly marked it
"do not run again". Kept here for full reproducibility of the corpus.

STATUS: settled in notebook, not yet promoted.
TODO: move the load_dataset / save_to_disk logic here, parameterized by
      cfg["dataset"]["hf_name"] and cfg["paths"]["raw"].
"""

from __future__ import annotations
