#!/usr/bin/env python3
"""Small dependency-free checks for the generated profile card."""

from __future__ import annotations

import json
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from read_metric import activity_state, wrapped_value  # noqa: E402


def main() -> None:
    metrics = json.loads(Path(".cache/metrics.json").read_text(encoding="utf-8"))
    profile = json.loads(Path("profile.json").read_text(encoding="utf-8"))
    svg = Path("github-terminal.svg").read_text(encoding="utf-8")
    visible_text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", svg)).split())

    assert svg.startswith("<svg "), "output is not SVG"
    login = metrics["login"]
    assert f"{login}@github" in svg, "profile header is missing"
    assert profile["role"] in visible_text, "role is missing"
    for line_number in (1, 2):
        quest_line = wrapped_value(profile["current_quest"], line_number).strip()
        fuel_line = wrapped_value(profile["fuel"], line_number).strip()
        if quest_line:
            assert quest_line in visible_text, "current quest is missing"
        if fuel_line:
            assert fuel_line in visible_text, "fuel is missing"
    assert profile["achievement"] in visible_text, "achievement is missing"
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
    assert 850 <= width <= 1100, "card width does not fit a GitHub profile"
    assert 500 <= height <= 700, "card height is outside the expected layout"

    colors = set(re.findall(r'fill="(#[0-9a-fA-F]{6})"', svg))
    assert len(colors) >= 32, "avatar was not rendered with a truecolor palette"

    print("profile card checks passed")


if __name__ == "__main__":
    main()
