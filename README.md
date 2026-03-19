# TinyLog Agent

Lightweight Python-based log triage daemon for VM/server environments.

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

## VM Monitoring Helper

- start: `./start_vm_monitor.sh`
- stop: `kill "$(cat vm_tinylog.pid)"`

Monitored files by default:
- `/var/log/syslog`
- `/var/log/auth.log`
- `/var/log/kern.log`
- `/var/log/dmesg`

Output: `./vm_tinylog.log`

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
