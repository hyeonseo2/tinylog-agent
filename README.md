# TinyLog Agent

Lightweight log monitoring agent with optional SLLM-assisted review.

## Features

- Tails multiple files in real-time
- Normalizes lines and groups similar error patterns
- Sliding-window threshold + cooldown to reduce noise
- Deterministic baseline + optional review rounds
- Optional SLLM backends for richer judgment:
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

## Run

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

The script monitors:
- `/var/log/syslog`
- `/var/log/auth.log`
- `/var/log/kern.log`
- `/var/log/dmesg`

Output is written to `./vm_tinylog.log` by default.

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
- `TINYLOG_BACKEND_TIMEOUT`
- `TINYLOG_BACKEND_BINARY`
- `TINYLOG_BACKEND_MODEL_PATH`
- `TINYLOG_OUTPUT_JSON`
- `TINYLOG_RUN_ONCE`

## Note on defaults

- CLI `--backend-timeout` and env `TINYLOG_BACKEND_TIMEOUT` both default to `600`.
- If no SLLM backend is configured, TinyLog keeps a deterministic fallback path.
