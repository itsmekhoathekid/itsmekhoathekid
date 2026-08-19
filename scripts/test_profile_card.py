#!/usr/bin/env python3
"""Small dependency-free checks for the generated profile card."""

from __future__ import annotations

import json
import re
from pathlib import Path


def main() -> None:
    metrics = json.loads(Path(".cache/metrics.json").read_text(encoding="utf-8"))
    svg = Path("github-terminal.svg").read_text(encoding="utf-8")

    assert svg.startswith("<svg "), "output is not SVG"
    login = metrics["login"]
    assert f"{login}@github" in svg, "profile header is missing"
    assert str(metrics["public_repos"]) in svg, "repository count is missing"
    assert str(metrics["total_stars"]) in svg, "star count is missing"
    assert f"github.com/{login}" in svg, "profile URL is missing"

    dimensions = re.search(r'<svg .*? width="(\d+)" height="(\d+)"', svg)
    assert dimensions, "SVG dimensions are missing"
    width, height = map(int, dimensions.groups())
    assert width >= 900 and height >= 500, "card may have wrapped or rendered empty"

    print("profile card checks passed")


if __name__ == "__main__":
    main()
