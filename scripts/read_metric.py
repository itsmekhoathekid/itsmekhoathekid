#!/usr/bin/env python3
"""Print one cached metric for Fastfetch command modules."""

from __future__ import annotations

import json
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def activity_state(hour: int) -> str:
    """Return the configured day/night label for a local clock hour."""
    return "asleep" if 0 <= hour < 8 else "awake"


def wrapped_value(value: str, line_number: int) -> str:
    """Wrap long profile values into two fixed-width terminal rows."""
    rows = textwrap.wrap(
        value,
        width=36,
        break_long_words=False,
        break_on_hyphens=False,
    ) or [""]
    if len(rows) > 2:
        remainder = " ".join(rows[1:])
        rows = [rows[0], textwrap.shorten(remainder, width=36, placeholder="…")]
    while len(rows) < 2:
        rows.append("")

    selected = rows[line_number - 1]
    return selected if line_number == 1 else f"{' ' * 18}{selected}"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: read_metric.py KEY")

    metrics = json.loads(Path(".cache/metrics.json").read_text(encoding="utf-8"))
    profile = json.loads(Path("profile.json").read_text(encoding="utf-8"))
    key = sys.argv[1]

    if key == "header":
        value = f"{metrics['login']}@github"
    elif key in {"current_quest_1", "current_quest_2"}:
        value = wrapped_value(profile["current_quest"], int(key[-1]))
    elif key in {"fuel_1", "fuel_2"}:
        value = wrapped_value(profile["fuel"], int(key[-1]))
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
