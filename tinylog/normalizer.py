from __future__ import annotations

import re

_UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
_IPV4_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_IPV6_RE = re.compile(r"(?i)(?:[0-9a-f]{1,4}:){2,7}[0-9a-f]{1,4}")
_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
_WHITESPACE_RE = re.compile(r"\s+")


def normalize(line: str) -> str:
    """Normalize a raw log line into a grouping-friendly representation."""

    cleaned = line.lower().strip()
    cleaned = _UUID_RE.sub("<uuid>", cleaned)
    cleaned = _IPV4_RE.sub("<ip>", cleaned)
    cleaned = _IPV6_RE.sub("<ip>", cleaned)
    cleaned = _NUMBER_RE.sub("<num>", cleaned)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned)
    return cleaned


def grouping_key(line: str) -> str:
    """Generate a coarse grouping key used by detector windows."""

    # Keep module/exception-like signals and stable tokens.
    normalized = normalize(line)
    # Remove bracketed timestamps and generic punctuation noise.
    normalized = re.sub(r"\[[^\]]+\]", "", normalized)
    normalized = re.sub(r"[^a-zA-Z0-9_<>\s]", " ", normalized)
    normalized = _WHITESPACE_RE.sub(" ", normalized).strip()
    return normalized
