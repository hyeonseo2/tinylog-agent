from __future__ import annotations

import json
import urllib.request


def query(
    prompt: str,
    *,
    host: str = "http://127.0.0.1:11434",
    model: str = "qwen2.5:0.5b",
    timeout: int = 30,
) -> str:
    """Call local Ollama /api/generate endpoint and return generated text."""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
        },
    }
    req = urllib.request.Request(
        f"{host}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if not isinstance(data, dict):
        raise RuntimeError("Unexpected response from ollama")

    return str(data.get("response", ""))
