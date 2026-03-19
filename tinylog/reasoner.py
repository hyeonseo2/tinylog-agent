from __future__ import annotations

from collections import Counter
from typing import Iterable, List

from .schemas import Hypothesis


def initial_hypothesis(incident: dict, evidence: Iterable[str]) -> Hypothesis:
    """Build a deterministic base hypothesis before LLM review."""

    evidence = list(evidence)
    base_summary = incident.get("summary", f"Potential incident in {incident.get('source', 'unknown source')}")
    terms = " ".join(evidence).lower().split()
    top_terms = [w for w, _ in Counter(terms).most_common(8) if len(w) > 4]

    queries = []
    # Heuristic follow-up queries to search in neighboring lines for causes.
    for term in top_terms[:3]:
        queries.append(f"contains:{term}")
        queries.append(f"contains:{term}_retry")

    # Deduplicate while preserving order.
    seen = set()
    deduped_queries: List[str] = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            deduped_queries.append(q)

    severity = min(5, 2 + len(evidence) // 4)
    risk = "medium" if incident.get("pattern_count", 0) < 10 else "high"

    rationale = (
        "Pattern repeated across buffered logs with error-like signature. "
        "Generated from deterministic frequency analysis and neighboring line context."
    )

    return Hypothesis(
        summary=base_summary,
        risk=risk,
        severity=severity,
        rationale=rationale,
        candidate_queries=deduped_queries[:6],
    )
