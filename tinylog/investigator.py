from __future__ import annotations

import re
from typing import Iterable, List


def collect_evidence(pattern: str, recent_logs: Iterable[dict], *, top_n: int = 20) -> List[str]:
    """Collect initial evidence from buffered log lines matching a pattern key."""

    evidence: list[str] = []
    for item in recent_logs:
        line = item["normalized"] if isinstance(item, dict) else item.normalized
        if pattern in line:
            evidence.append(item["raw"] if isinstance(item, dict) else item.raw)
            if len(evidence) >= top_n:
                break
    return evidence


def _run_single_query(query: str, logs: Iterable[dict]) -> list[str]:
    if ":" in query:
        kind, expr = query.split(":", 1)
        kind = kind.strip().lower()
        expr = expr.strip().lower()
    else:
        kind, expr = "contains", query.strip().lower()

    results = []
    for item in logs:
        raw = item["raw"] if isinstance(item, dict) else item.raw
        text = raw.lower()

        if not expr:
            continue

        if kind == "contains":
            if expr in text:
                results.append(raw)
        elif kind == "regex":
            try:
                if re.search(expr, raw, re.IGNORECASE):
                    results.append(raw)
            except re.error:
                if expr in text:
                    results.append(raw)
        elif kind == "startswith":
            if text.startswith(expr):
                results.append(raw)
    return results


def run_queries(queries: List[str], recent_logs: Iterable[dict], *, max_per_query: int = 20) -> dict:
    """Run additional review-guided evidence queries over the buffered logs."""

    payload = {}
    for q in queries:
        matched = _run_single_query(q, recent_logs)
        payload[q] = matched[:max_per_query]
    return payload
