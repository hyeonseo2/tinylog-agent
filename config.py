from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass
class TinyLogConfig:
    files: list[str]
    window_seconds: int = 120
    threshold: int = 3
    cooldown_seconds: int = 300
    evidence_window: int = 300
    max_recent_lines: int = 500
    review_rounds: int = 2
    backend: str = "none"  # none, ollama, llamacpp
    backend_host: str = "http://127.0.0.1:11434"
    backend_model: str = "qwen2.5:0.5b"
    backend_timeout: int = 600
    backend_binary: str = "llama"
    backend_model_path: str = ""
    output_json: bool = False
    run_once: bool = False

    @classmethod
    def from_env(cls) -> "TinyLogConfig":
        files = [x.strip() for x in _env("TINYLOG_FILES", "").split(",") if x.strip()]
        return cls(
            files=files,
            window_seconds=int(_env("TINYLOG_WINDOW_SECONDS", "120")),
            threshold=int(_env("TINYLOG_THRESHOLD", "3")),
            cooldown_seconds=int(_env("TINYLOG_COOLDOWN_SECONDS", "300")),
            evidence_window=int(_env("TINYLOG_EVIDENCE_WINDOW", "300")),
            max_recent_lines=int(_env("TINYLOG_MAX_RECENT_LINES", "500")),
            review_rounds=max(1, int(_env("TINYLOG_REVIEW_ROUNDS", "2"))),
            backend=_env("TINYLOG_BACKEND", "none").lower(),
            backend_host=_env("TINYLOG_BACKEND_HOST", "http://127.0.0.1:11434"),
            backend_model=_env("TINYLOG_BACKEND_MODEL", "qwen2.5:0.5b"),
            backend_timeout=int(_env("TINYLOG_BACKEND_TIMEOUT", "600")),
            backend_binary=_env("TINYLOG_BACKEND_BINARY", "llama"),
            backend_model_path=_env("TINYLOG_BACKEND_MODEL_PATH", ""),
            output_json=_env("TINYLOG_OUTPUT_JSON", "false").lower() in {"1", "true", "yes", "on"},
            run_once=_env("TINYLOG_RUN_ONCE", "false").lower() in {"1", "true", "yes", "on"},
        )

    @classmethod
    def from_file(cls, path: str) -> "TinyLogConfig":
        # very small env-like parser to avoid dependencies:
        data = {}
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()

        os.environ.update({k: v for k, v in data.items()})
        return cls.from_env()


def build_llm_backend(cfg: TinyLogConfig):
    if cfg.backend == "ollama":
        from tinylog.backends.ollama_client import query as ollama_query

        return lambda prompt: ollama_query(
            prompt,
            host=cfg.backend_host,
            model=cfg.backend_model,
            timeout=cfg.backend_timeout,
        )

    if cfg.backend == "llamacpp":
        from tinylog.backends.llamacpp_client import query as llama_query

        return lambda prompt: llama_query(
            prompt,
            binary=cfg.backend_binary,
            model_path=cfg.backend_model_path,
        )

    return None
