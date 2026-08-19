#!/usr/bin/env python3
"""Update a field in profile.json without requiring jq."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROFILE_PATH = Path("profile.json")
EDITABLE_FIELDS = {"role", "current_quest", "status", "fuel", "achievement"}


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: update_profile.py FIELD VALUE")

    field, value = sys.argv[1:]
    if field not in EDITABLE_FIELDS:
        allowed = ", ".join(sorted(EDITABLE_FIELDS))
        raise SystemExit(f"unsupported field {field!r}; choose one of: {allowed}")
    if not value.strip():
        raise SystemExit("value cannot be empty")

    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    profile[field] = value.strip()
    PROFILE_PATH.write_text(
        json.dumps(profile, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"updated {field}: {profile[field]}")


if __name__ == "__main__":
    main()
