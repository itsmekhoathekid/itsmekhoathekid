#!/usr/bin/env python3
"""Small dependency-free checks for the generated profile card."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from read_metric import activity_state  # noqa: E402


def main() -> None:
    metrics = json.loads(Path(".cache/metrics.json").read_text(encoding="utf-8"))
    profile = json.loads(Path("profile.json").read_text(encoding="utf-8"))
    svg = Path("github-terminal.svg").read_text(encoding="utf-8")

    assert svg.startswith("<svg "), "output is not SVG"
    login = metrics["login"]
    assert f"{login}@github" in svg, "profile header is missing"
    assert profile["role"] in svg, "role is missing"
    assert profile["current_quest"] in svg, "current quest is missing"
    assert profile["achievement"] in svg, "achievement is missing"
    assert "probably awake" in svg or "probably asleep" in svg, "time status is missing"
    assert str(metrics["public_repos"]) in svg, "repository count is missing"
    assert str(metrics["total_stars"]) in svg, "star count is missing"
    assert metrics["updated_at"].endswith("ICT"), "last sync is not in Vietnam time"
    assert activity_state(0) == "asleep"
    assert activity_state(7) == "asleep"
    assert activity_state(8) == "awake"
    assert activity_state(23) == "awake"

    dimensions = re.search(r'<svg .*? width="(\d+)" height="(\d+)"', svg)
    assert dimensions, "SVG dimensions are missing"
    width, height = map(int, dimensions.groups())
    assert width >= 1000 and height >= 500, "card may have wrapped or rendered empty"

    print("profile card checks passed")


if __name__ == "__main__":
    main()
