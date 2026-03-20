# TinyLog Agent

Lightweight Python-based log triage daemon for multi-source server logs.

> **Project size:** ~`< 1000` Python LOC (currently about `985` lines) so it stays simple, auditable, and easy to run.

## Highlights

- Multi-file real-time log tailing (`/var/log/syslog`, `auth.log`, `kern.log`, `dmesg`, etc.)
- Pattern normalization to reduce noise and group similar events
- Sliding-window threshold + cooldown controls
- Deterministic fallback pipeline for reliability when SLLM is unavailable
- Optional SLLM-assisted review for richer incident judgment
  - `ollama`
  - `llamacpp`

## Project Structure

```text
tinylog-agent/
├── tinylog/
│   ├── __init__.py
│   ├── backends/
│   │   ├── ollama_client.py
│   │   └── llamacpp_client.py
│   ├── detector.py
│   ├── investigator.py
│   ├── normalizer.py
│   ├── reasoner.py
│   ├── reporter.py
│   ├── reviewer.py
│   ├── schemas.py
│   └── tailer.py
├── config.py
├── main.py
├── README.md
├── requirements.txt
├── pyproject.toml
├── start_vm_monitor.sh
├── LICENSE
└── .gitignore
```

## Pipeline (high-level)

TinyLog is a simple 5-step incident triage pipeline:

```text
[tailer] --> [detector] --> [investigator] --> [reasoner] --> [reviewer] --> [reporter]
    |             |             |              |              |             |
    |             |             |              |              |             |
    v             v             v              v              v             v
- reads files  - finds         - gathers      - builds        - LLM review  - prints report
              repeating       matching logs    hypothesis    + final        in
              patterns         around pattern    + follow-up                  JSON/console
              in time         by pattern
              window
```

### Module roles

- `tinylog.tailer` : stream lines from one or more files (like `tail -f`).
- `tinylog.detector` : detect error-like patterns and apply window + cooldown filtering.
- `tinylog.investigator` : collect matching evidence and run follow-up search queries.
- `tinylog.reasoner` : create the initial hypothesis and candidate follow-up queries.
- `tinylog.reviewer` : call SLLM (or deterministic fallback) to get `verdict` and `decision`.
- `tinylog.reporter` : render output (console or JSON).

When LLM is not available, fallback outputs still stay structured for automation.

## Quick Start

### One-shot mode

```bash
python3 main.py --files /tmp/app.log /tmp/sys.log --once --output json
```

### Continuous mode

```bash
python3 main.py --files /var/log/syslog /var/log/auth.log --backend ollama
```

### Install and run as CLI

```bash
pip install -e .
tinylog-agent --files /var/log/syslog --backend none
```

## Log Monitoring Helper

- start: `./start_tinylog_monitor.sh` (legacy: `./start_vm_monitor.sh`)
- stop: `kill "$(cat tinylog_monitor.pid)"`

Monitored files by default:
- `/var/log/syslog`
- `/var/log/auth.log`
- `/var/log/kern.log`
- `/var/log/dmesg`

Output: `./tinylog_monitor.log`

## Environment Variables

- `TINYLOG_FILES`
- `TINYLOG_WINDOW_SECONDS`
- `TINYLOG_THRESHOLD`
- `TINYLOG_COOLDOWN_SECONDS`
- `TINYLOG_MAX_RECENT_LINES`
- `TINYLOG_REVIEW_ROUNDS`
- `TINYLOG_BACKEND` (`none`, `ollama`, `llamacpp`)
- `TINYLOG_BACKEND_HOST`
- `TINYLOG_BACKEND_MODEL`
- `TINYLOG_BACKEND_TIMEOUT` *(default: 600)*
- `TINYLOG_BACKEND_BINARY`
- `TINYLOG_BACKEND_MODEL_PATH`
- `TINYLOG_OUTPUT_JSON`
- `TINYLOG_RUN_ONCE`

## Design notes

- This repo intentionally stays minimal to keep behavior transparent and maintenance low.
- If SLLM is not configured, output remains usable through deterministic fallback paths.
- JSON output supports lightweight downstream automation and parsing.
