#!/usr/bin/env python3
"""Publish profile settings while GitHub Actions owns the generated SVG."""

from __future__ import annotations

import subprocess
import sys


MAX_PUSH_ATTEMPTS = 5


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result


def main() -> None:
    branch = git("branch", "--show-current").stdout.strip()
    if branch != "main":
        raise RuntimeError(f"Expected branch main, found {branch or 'detached HEAD'}")

    # A preview belongs in .cache/. Never commit the bot-generated SVG locally.
    dirty = git("status", "--porcelain", "--untracked-files=no").stdout.splitlines()
    unrelated = [line for line in dirty if line[3:] != "profile.json"]
    if unrelated:
        raise RuntimeError(
            "Other tracked files have local changes. Commit or stash them before "
            "make sync: " + ", ".join(line[3:] for line in unrelated)
        )

    changed = bool(git("diff", "HEAD", "--", "profile.json").stdout)
    if changed:
        git("add", "--", "profile.json")
        git("commit", "-m", "chore: update profile settings", "--only", "--", "profile.json")

    for attempt in range(1, MAX_PUSH_ATTEMPTS + 1):
        git("fetch", "origin", "main")
        rebase = git("rebase", "origin/main", check=False)
        if rebase.returncode:
            git("rebase", "--abort", check=False)
            raise RuntimeError(
                "Remote profile settings conflict with local changes. "
                "Your commits are intact; resolve this manually.\n"
                + (rebase.stderr.strip() or rebase.stdout.strip())
            )

        pushed_paths = git("diff", "--name-only", "origin/main..HEAD").stdout.splitlines()
        render_triggered = any(
            path in {"profile.json", "github-fastfetch.jsonc", ".github/workflows/profile-card.yml"}
            or path.startswith("scripts/")
            for path in pushed_paths
        )
        push = git("push", "origin", "main", check=False)
        if push.returncode == 0:
            if push.stdout.strip():
                print(push.stdout.strip())
            if render_triggered:
                print("Profile published. GitHub Actions will update github-terminal.svg.")
            else:
                dispatch = subprocess.run(
                    ["gh", "workflow", "run", "profile-card.yml", "--ref", "main"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if dispatch.returncode:
                    raise RuntimeError(
                        "Git branch is synced, but workflow dispatch failed: "
                        + (dispatch.stderr.strip() or dispatch.stdout.strip())
                    )
                print("Profile synced. Requested a fresh metrics render on GitHub Actions.")
            return

        rejected = push.stderr.lower()
        if "fetch first" not in rejected and "non-fast-forward" not in rejected:
            raise RuntimeError(push.stderr.strip() or push.stdout.strip())
        print(f"Remote updated during push; retrying ({attempt}/{MAX_PUSH_ATTEMPTS})...")

    raise RuntimeError("Remote kept changing; please run make sync again.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(f"sync failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
