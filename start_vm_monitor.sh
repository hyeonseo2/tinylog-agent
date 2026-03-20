#!/usr/bin/env bash
# Backward-compatible wrapper for the renamed launcher.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/start_tinylog_monitor.sh "$@"
