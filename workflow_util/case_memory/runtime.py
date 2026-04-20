from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .build_casebank import build_casebank
from .prompt_format import build_reference_block
from .retriever import CaseRetriever


DEFAULT_CASEBANK_PATH = Path("/workspace/workflow_data/casebank.jsonl")
DEFAULT_REPORTS_DIR = Path("/workspace/workflow_data/pricing_reports")


def _env_truthy(name: str, default: str = "") -> bool:
    v = os.environ.get(name, default)
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


@lru_cache(maxsize=1)
def _get_retriever(casebank_path: str) -> Optional[CaseRetriever]:
    path = Path(casebank_path)
    if not path.exists():
        return None
    return CaseRetriever(path)


def get_reference_cases_block(query_text: str) -> str:
    """Return a compact few-shot reference block, or empty string if disabled/unavailable."""

    enabled = _env_truthy("CASE_MEMORY_ENABLED", default="1")
    if not enabled:
        return ""

    casebank_path = os.environ.get("CASE_MEMORY_PATH", str(DEFAULT_CASEBANK_PATH))
    top_k = int(os.environ.get("CASE_MEMORY_TOP_K", "2"))

    # Optional auto-build (off by default to avoid surprise regeneration)
    if not Path(casebank_path).exists() and _env_truthy("CASE_MEMORY_AUTO_BUILD", default="0"):
        if DEFAULT_REPORTS_DIR.exists():
            build_casebank(DEFAULT_REPORTS_DIR, casebank_path)

    retriever = _get_retriever(casebank_path)
    if retriever is None:
        return ""

    retrieved = retriever.retrieve(query_text, top_k=top_k)
    return build_reference_block([r.case for r in retrieved if r.score > 0])
