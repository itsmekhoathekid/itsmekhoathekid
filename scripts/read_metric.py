#!/usr/bin/env python3
"""Print one cached metric for Fastfetch command modules."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: read_metric.py KEY")

    metrics = json.loads(Path(".cache/metrics.json").read_text(encoding="utf-8"))
    key = sys.argv[1]

    if key == "header":
        value = f"{metrics['login']}@github"
    else:
        value = metrics.get(key)

    if value is None:
        value = "N/A"

    print(value, end="")


if __name__ == "__main__":
    main()
