from __future__ import annotations

import argparse
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Dict, List

from config import TinyLogConfig, build_llm_backend
from tinylog.detector import SlidingWindowDetector, is_error
from tinylog.investigator import collect_evidence, run_queries
from tinylog.normalizer import grouping_key
from tinylog.reasoner import initial_hypothesis
from tinylog.reporter import output_report
from tinylog.reviewer import review_final, review_initial
from tinylog.schemas import Incident, IncidentReport
from tinylog.tailer import follow


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TinyLog Agent")
    p.add_argument("--config", type=str, default="", help="Optional KEY=VALUE config file")
    p.add_argument("--files", type=str, nargs="+", help="Paths to monitor")
    p.add_argument("--window-seconds", type=int, default=120)
    p.add_argument("--threshold", type=int, default=3)
    p.add_argument("--cooldown-seconds", type=int, default=300)
    p.add_argument("--max-recent-lines", type=int, default=500)
    p.add_argument("--review-rounds", type=int, default=2, help="How many iterative review rounds to run")
    p.add_argument("--output", choices=["console", "json"], default="console")
    p.add_argument("--backend", choices=["none", "ollama", "llamacpp"], default="none")
    p.add_argument("--backend-host", type=str, default="http://127.0.0.1:11434")
    p.add_argument("--backend-model", type=str, default="qwen2.5:0.5b")
    p.add_argument("--backend-timeout", type=int, default=600)
    p.add_argument("--backend-binary", type=str, default="llama")
    p.add_argument("--backend-model-path", type=str, default="")
    p.add_argument("--once", action="store_true", help="Read existing files only and exit")
    return p.parse_args()


def _build_config(args: argparse.Namespace) -> TinyLogConfig:
    if args.config:
        cfg = TinyLogConfig.from_file(args.config)
    else:
        cfg = TinyLogConfig.from_env()

    if args.files:
        cfg.files = args.files
    cfg.window_seconds = args.window_seconds
    cfg.threshold = args.threshold
    cfg.cooldown_seconds = args.cooldown_seconds
    cfg.max_recent_lines = args.max_recent_lines
    cfg.review_rounds = max(1, args.review_rounds)
    cfg.backend = args.backend
    cfg.backend_host = args.backend_host
    cfg.backend_model = args.backend_model
    cfg.backend_timeout = args.backend_timeout
    cfg.backend_binary = args.backend_binary
    cfg.backend_model_path = args.backend_model_path
    cfg.output_json = args.output == "json"
    cfg.run_once = args.once
    return cfg


def _incident_summary(source: str, pattern: str, count: int, evidence_count: int) -> Incident:
    return Incident(
        incident_id=str(uuid.uuid4()),
        source=source,
        pattern=pattern,
        timestamp=time.time(),
        trigger_count=count,
        evidence_count=evidence_count,
    )


def run_pipeline(cfg: TinyLogConfig) -> None:
    if not cfg.files:
        raise RuntimeError("No log files configured. Use --files or TINYLOG_FILES.")

    for f in cfg.files:
        Path(f).parent.mkdir(parents=True, exist_ok=True)

    detector = SlidingWindowDetector(
        window_seconds=cfg.window_seconds,
        threshold=cfg.threshold,
        cooldown_seconds=cfg.cooldown_seconds,
    )

    llm_backend = build_llm_backend(cfg)
    recent_logs = deque(maxlen=cfg.max_recent_lines)

    print(f"TinyLog Agent started. monitoring {len(cfg.files)} files")

    for source, line in follow(
        cfg.files,
        follow=not cfg.run_once,
        start_at_end=not cfg.run_once,
    ):
        now = time.time()
        normalized = grouping_key(line)
        recent_logs.append({"ts": now, "source": source, "raw": line, "normalized": normalized})

        if not is_error(line):
            continue

        pattern = normalized
        count = detector.update_window(pattern, event_ts=now)
        if not detector.should_trigger(pattern, count=count, event_ts=now):
            continue

        evidence = collect_evidence(pattern, list(recent_logs), top_n=20)
        incident_payload = {
            "pattern": pattern,
            "pattern_count": count,
            "source": source,
            "summary": f"Repeated error pattern observed in {source}",
        }

        hypothesis = initial_hypothesis(incident_payload, evidence)
        review = review_initial(hypothesis, incident_payload, evidence, llm_backend=llm_backend, review_round=1)
        review_trace: List[Dict[str, Any]] = [
            {
                "round": 1,
                "verdict": review.verdict,
                "confidence": review.confidence,
                "rationale": review.rationale,
                "next_queries": list(review.next_queries),
                "gaps": list(review.gaps),
            }
        ]

        combined_evidence = list(evidence)
        all_extra_evidence: Dict[str, list[str]] = {}

        for round_no in range(2, cfg.review_rounds + 1):
            extra_queries = review.next_queries or []
            if not extra_queries:
                break

            extra_evidence = run_queries(extra_queries, recent_logs)
            for q, lines in extra_evidence.items():
                all_extra_evidence[q] = list(lines)
                if lines:
                    combined_evidence.extend(lines[:3])

            prior_summary = (
                f"Round {round_no - 1} verdict={review.verdict}, "
                f"rationale={review.rationale}, gaps={review.gaps}"
            )
            review = review_initial(
                hypothesis,
                incident_payload,
                combined_evidence,
                llm_backend=llm_backend,
                review_round=round_no,
                prior_summary=prior_summary,
            )
            review_trace.append(
                {
                    "round": round_no,
                    "verdict": review.verdict,
                    "confidence": review.confidence,
                    "rationale": review.rationale,
                    "next_queries": list(review.next_queries),
                    "gaps": list(review.gaps),
                }
            )

        final_judgment = review_final(
            hypothesis,
            incident_payload,
            combined_evidence,
            all_extra_evidence,
            llm_backend=llm_backend,
        )

        print("Review Trace:")
        for item in review_trace:
            print(
                f"  - Round {item['round']}: verdict={item['verdict']} "
                f"confidence={item['confidence']:.2f} gaps={item['gaps']}"
            )

        report = IncidentReport(
            incident=_incident_summary(
                source=source,
                pattern=pattern,
                count=count,
                evidence_count=len(combined_evidence),
            ),
            hypothesis=hypothesis,
            initial_review=review,
            final_judgment=final_judgment,
        )
        output_report(report, json_output=cfg.output_json)


def main() -> None:
    args = _parse_args()
    config = _build_config(args)
    run_pipeline(config)


if __name__ == "__main__":
    main()
