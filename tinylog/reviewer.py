from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List

from .schemas import FinalJudgment, Review


_JSON_OBJ_RE = re.compile(r"\{[\s\S]*\}")


def _extract_json(text: str) -> Dict[str, Any] | None:
    match = _JSON_OBJ_RE.search(text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def _build_payload(
    hypothesis: Any,
    incident: dict,
    evidence: Iterable[str],
    *,
    review_round: int = 1,
    prior_summary: str = "",
) -> str:
    e = list(evidence)
    lines = "\n".join(f"- {x}" for x in e[:12]) if e else "(no evidence yet)"
    prior = f"PREVIOUS REVIEW ROUND NOTES: {prior_summary}\n\n" if prior_summary else ""
    return (
        "You are a lightweight incident reviewer. "
        "Return ONLY JSON for consistency.\n\n"
        f"REVIEW ROUND: {review_round}\n"
        f"{prior}"
        f"INCIDENT: {incident}\n"
        f"HYPOTHESIS: {hypothesis}\n"
        f"EVIDENCE:\n{lines}\n\n"
        "Return JSON only. Schema:\n"
        "{\"verdict\": string, \"confidence\": 0..1 float, \"rationale\": string, \"next_queries\": [string], \"gaps\": [string]}\n"
    )


def _build_final_payload(
    hypothesis: Any,
    incident: dict,
    evidence: Iterable[str],
    extra_evidence: Dict[str, Iterable[str]],
    *,
    review_round: int = 1,
    prior_summary: str = "",
) -> str:
    base = _build_payload(
        hypothesis,
        incident,
        evidence,
        review_round=review_round,
        prior_summary=prior_summary,
    )
    extras = "\n".join(
        f"{k}:\n" + "\n".join(f"  - {x}" for x in list(v)[:6])
        for k, v in extra_evidence.items()
    )
    return (
        base
        + "\nextra_evidence:\n"
        + (extras or "(none)")
        + "\n\nReturn JSON only. Schema:\n"
        + "{\"decision\": one of [needs_followup, escalate, acknowledge, defer, ignore], \"confidence\": 0..1 float, \"summary\": string, \"rationale\": string, \"evidence_gaps\": [string]}\n"
    )


def _coerce_prob(v: Any) -> float:
    try:
        v = float(v)
    except Exception:
        return 0.5
    return max(0.0, min(1.0, v))


def _coerce_str_list(value: Any) -> list[str]:
    """Normalize a value to a list[str]."""
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                # keep best effort: convert common object payloads to compact text
                text = item.get("query") or item.get("item") or item.get("reason")
                if text:
                    out.append(str(text))
                else:
                    out.append(json.dumps(item, ensure_ascii=False))
        return out
    if isinstance(value, tuple):
        return _coerce_str_list(list(value))
    return []


def _normalize_decision(raw: Any) -> str:
    allowed = {"needs_followup", "escalate", "acknowledge", "defer", "ignore"}
    if raw is None:
        return "needs_followup"
    val = str(raw).strip().lower()
    if val in allowed:
        return val
    # handle accidental drift like "contains:...: YES"
    if val.startswith("contains:") and "yes" in val:
        return "needs_followup"
    if "yes" in val and any(tok in val for tok in ["2026", "contains:", "error"]):
        return "needs_followup"
    return "needs_followup"


def _coerce_review_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Force the parsed payload into expected keys/types for deterministic downstream."""
    return {
        "verdict": str(payload.get("verdict", "defer")).strip() or "defer",
        "confidence": _coerce_prob(payload.get("confidence", 0.5)),
        "rationale": str(payload.get("rationale", "No rationale returned")),
        "next_queries": _coerce_str_list(payload.get("next_queries", [])),
        "gaps": _coerce_str_list(payload.get("gaps", [])),
    }


def _coerce_final_payload(payload: dict[str, Any]) -> dict[str, Any]:
    decision = _normalize_decision(payload.get("decision"))
    confidence = _coerce_prob(payload.get("confidence", 0.5))
    summary = str(payload.get("summary", "Final judgment produced from all gathered evidence.")).strip()
    rationale = str(payload.get("rationale", "No rationale returned by SLLM.")).strip()
    evidence_gaps = _coerce_str_list(payload.get("evidence_gaps", []))
    if not evidence_gaps and decision == "needs_followup":
        # keep non-empty placeholder so consumers can distinguish empty-vs-missing
        evidence_gaps = []
    return {
        "decision": decision,
        "confidence": confidence,
        "summary": summary or "Final judgment produced from all gathered evidence.",
        "rationale": rationale or "No rationale returned by SLLM.",
        "evidence_gaps": evidence_gaps,
    }


def review_initial(
    hypothesis,
    incident,
    evidence,
    *,
    llm_backend=None,
    review_round: int = 1,
    prior_summary: str = "",
) -> Review:
    if llm_backend is None:
        return Review(
            verdict="defer",
            confidence=0.5,
            rationale="No SLLM backend configured; using deterministic review fallback.",
            next_queries=getattr(hypothesis, "candidate_queries", []),
            gaps=["backend missing"],
        )

    try:
        response = llm_backend(
            _build_payload(
                hypothesis,
                incident,
                evidence,
                review_round=review_round,
                prior_summary=prior_summary,
            )
        )
        payload = _extract_json(response) or {}
        coerced = _coerce_review_payload(payload)
        return Review(
            verdict=coerced["verdict"],
            confidence=coerced["confidence"],
            rationale=coerced["rationale"],
            next_queries=coerced["next_queries"],
            gaps=coerced["gaps"],
        )
    except Exception:
        return Review(
            verdict="defer",
            confidence=0.35,
            rationale="SLLM review failed; using fallback review path.",
            next_queries=getattr(hypothesis, "candidate_queries", []),
            gaps=["sllm_error"],
        )


def review_final(hypothesis, incident, evidence, extra_evidence, *, llm_backend=None) -> FinalJudgment:
    if llm_backend is None:
        gaps = [
            f"No additional evidence for query: {k}" for k, v in extra_evidence.items() if not v
        ]
        return FinalJudgment(
            decision="needs_followup",
            confidence=0.55,
            summary="SLLM disabled. Initial hypothesis retained as preliminary.",
            rationale="Review backend unavailable in this environment.",
            evidence_gaps=gaps,
        )

    try:
        response = llm_backend(
            _build_final_payload(
                hypothesis,
                incident,
                evidence,
                extra_evidence,
            )
        )
        payload = _extract_json(response) or {}
        coerced = _coerce_final_payload(payload)
        return FinalJudgment(
            decision=coerced["decision"],
            confidence=coerced["confidence"],
            summary=coerced["summary"],
            rationale=coerced["rationale"],
            evidence_gaps=coerced["evidence_gaps"],
        )
    except Exception:
        return FinalJudgment(
            decision="needs_followup",
            confidence=0.45,
            summary="SLLM final review failed; kept deterministic defaults.",
            rationale="Fallback due to SLLM final review failure.",
            evidence_gaps=["sllm_error"],
        )
