from __future__ import annotations

import subprocess


def query(
    prompt: str,
    *,
    binary: str = "llama",
    model_path: str = "",
    timeout: int = 30,
) -> str:
    """Call a local llama.cpp-compatible binary and return stdout text."""

    cmd = [binary, "-p", prompt, "-n", "512", "-t", "2", "-ngl", "0"]
    if model_path:
        cmd.extend(["-m", model_path])

    proc = subprocess.run(
        cmd,
        input=None,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc.stdout.strip()
