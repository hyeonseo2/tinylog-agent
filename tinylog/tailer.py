from __future__ import annotations

import os
import time
from collections import deque
from pathlib import Path
from typing import Deque, Iterator, Tuple


def _open_file_for_tail(path: str):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    return open(path, "r", encoding="utf-8", errors="replace")


def follow(files, *, follow: bool = True, sleep_seconds: float = 1.0, start_at_end: bool = True) -> Iterator[Tuple[str, str]]:
    """Yield (source, line) tuples as lines appear in files.

    This is a tiny multi-log tailer for local files; it keeps all files open and
    polls for new lines in a simple round-robin loop.
    """

    handles: dict[str, object] = {}
    positions: dict[str, int] = {}
    backlog: dict[str, Deque[str]] = {}

    for path in files:
        p = str(Path(path))
        if not os.path.exists(p):
            # Lazily wait for files that may be created later.
            handle = None
        else:
            handle = _open_file_for_tail(p)
            if start_at_end:
                handle.seek(0, os.SEEK_END)
            positions[p] = handle.tell()
            backlog[p] = deque(maxlen=32)
        handles[p] = handle

    open_paths = list(handles.keys())

    while True:
        emitted = False

        for path in open_paths:
            handle = handles[path]
            if handle is None:
                if os.path.exists(path):
                    handle = _open_file_for_tail(path)
                    if start_at_end:
                        handle.seek(0, os.SEEK_END)
                    positions[path] = handle.tell()
                    backlog[path] = deque(maxlen=32)
                    handles[path] = handle
                else:
                    continue

            while True:
                line = handle.readline()
                if not line:
                    break
                emitted = True
                positions[path] = handle.tell()
                yield path, line.rstrip("\n")

        if not follow and not emitted:
            return

        if not emitted:
            time.sleep(sleep_seconds)

