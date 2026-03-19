from __future__ import annotations

import json
import time
from typing import Optional

from .schemas import IncidentReport


def render_console(report: IncidentReport) -> str:
    return (
        "\n[Incident Detected]\n"
        f"Incident ID: {report.incident.incident_id}\n"
        f"Source: {report.incident.source}\n"
        f"Pattern: {report.incident.pattern}\n"
        f"Trigger Count: {report.incident.trigger_count}\n"
        f"Initial Hypothesis: {report.hypothesis.summary} | risk={report.hypothesis.risk} severity={report.hypothesis.severity}\n"
        f"Initial Review: {report.initial_review.verdict} (confidence={report.initial_review.confidence:.2f})\n"
        f"Rationale: {report.initial_review.rationale}\n"
        f"Final Decision: {report.final_judgment.decision} (confidence={report.final_judgment.confidence:.2f})\n"
        f"Final Rationale: {report.final_judgment.rationale}\n"
        f"Evidence gaps: {', '.join(report.final_judgment.evidence_gaps) or 'none'}\n"
    )


def output_report(report: IncidentReport, *, json_output: bool = False) -> Optional[str]:
    if json_output:
        payload = report.as_dict()
        payload["incident"]["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        text = json.dumps(payload, indent=2)
        print(text)
        return text

    text = render_console(report)
    print(text)
    return text
