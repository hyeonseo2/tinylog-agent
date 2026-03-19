from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class LogLine:
    ts: float
    source: str
    raw: str
    normalized: str
    matched_patterns: List[str] = field(default_factory=list)


@dataclass
class Incident:
    incident_id: str
    source: str
    pattern: str
    timestamp: float
    trigger_count: int
    evidence_count: int


@dataclass
class Hypothesis:
    summary: str
    risk: str
    severity: int
    rationale: str
    candidate_queries: List[str] = field(default_factory=list)


@dataclass
class Review:
    verdict: str
    confidence: float
    rationale: str
    next_queries: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)


@dataclass
class FinalJudgment:
    decision: str
    confidence: float
    summary: str
    rationale: str
    evidence_gaps: List[str] = field(default_factory=list)


@dataclass
class IncidentReport:
    incident: Incident
    hypothesis: Hypothesis
    initial_review: Review
    final_judgment: FinalJudgment

    def as_dict(self) -> Dict[str, Any]:
        return {
            "incident": asdict(self.incident),
            "hypothesis": asdict(self.hypothesis),
            "initial_review": asdict(self.initial_review),
            "final_judgment": asdict(self.final_judgment),
        }

