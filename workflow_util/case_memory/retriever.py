from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple


def _normalize_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\s+", "", s)
    return s


def _char_ngrams(s: str, n: int = 2) -> List[str]:
    s = _normalize_text(s)
    if not s:
        return []
    if len(s) < n:
        return [s]
    return [s[i : i + n] for i in range(len(s) - n + 1)]


def _vectorize(s: str) -> Counter[str]:
    return Counter(_char_ngrams(s, 2))


def _cosine(a: Counter[str], b: Counter[str]) -> float:
    dot = 0.0
    for k, av in a.items():
        dot += av * b.get(k, 0)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _case_to_retrieval_text(case: Dict[str, Any]) -> str:
    headers = "\n".join(case.get("section_headers", []) or [])
    service_names = "\n".join([(x.get("name") or "") for x in (case.get("service_lines", []) or [])])
    preview = case.get("raw_preview", "") or ""
    case_id = case.get("case_id", "") or ""
    return f"{case_id}\n{headers}\n{service_names}\n{preview}"


@dataclass(frozen=True)
class RetrievedCase:
    case: Dict[str, Any]
    score: float


class CaseRetriever:
    def __init__(self, casebank_path: str | Path):
        self.casebank_path = Path(casebank_path)
        self._cases: List[Dict[str, Any]] = []
        self._vecs: List[Counter[str]] = []
        self._load()

    def _load(self) -> None:
        cases: List[Dict[str, Any]] = []
        with self.casebank_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                cases.append(json.loads(line))

        self._cases = cases
        self._vecs = [_vectorize(_case_to_retrieval_text(c)) for c in self._cases]

    @property
    def cases(self) -> Sequence[Dict[str, Any]]:
        return self._cases

    def retrieve(self, query_text: str, top_k: int = 3) -> List[RetrievedCase]:
        qv = _vectorize(query_text)
        scored: List[RetrievedCase] = []
        for case, cv in zip(self._cases, self._vecs):
            scored.append(RetrievedCase(case=case, score=_cosine(qv, cv)))

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[: max(0, top_k)]
