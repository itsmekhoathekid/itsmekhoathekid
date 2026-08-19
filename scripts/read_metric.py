#!/usr/bin/env python3
"""Print one cached metric for Fastfetch command modules."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def activity_state(hour: int) -> str:
    """Return the configured day/night label for a local clock hour."""
    return "asleep" if 0 <= hour < 8 else "awake"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: read_metric.py KEY")

    metrics = json.loads(Path(".cache/metrics.json").read_text(encoding="utf-8"))
    profile = json.loads(Path("profile.json").read_text(encoding="utf-8"))
    key = sys.argv[1]

    if key == "header":
        value = f"{metrics['login']}@github"
    elif key == "timezone_status":
        local_hour = datetime.now(ZoneInfo(profile["timezone"])).hour
        state = activity_state(local_hour)
        value = f"{profile['timezone_label']} — probably {state}"
    elif key in profile:
        value = profile[key]
    else:
        value = metrics.get(key)

    if value is None:
        value = "N/A"

    print(value, end="")


if __name__ == "__main__":
    main()
