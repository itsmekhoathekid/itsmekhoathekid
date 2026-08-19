#!/usr/bin/env python3
"""Fetch public GitHub profile metrics and the current avatar."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


API = "https://api.github.com"
CACHE_DIR = Path(".cache")
TOKEN = os.environ.get("GH_TOKEN", "").strip()
USERNAME = os.environ.get("GITHUB_USER", "").strip()


def request_json(url: str, *, body: dict[str, Any] | None = None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-profile-terminal-card",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def download(url: str, destination: Path) -> None:
    headers = {
        "Accept": "image/*",
        "User-Agent": "github-profile-terminal-card",
    }
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        destination.write_bytes(response.read())


def fetch_all_repositories(login: str) -> list[dict[str, Any]]:
    repositories: list[dict[str, Any]] = []
    page = 1
    while True:
        query = urllib.parse.urlencode(
            {"type": "owner", "sort": "updated", "per_page": 100, "page": page}
        )
        batch = request_json(f"{API}/users/{login}/repos?{query}")
        repositories.extend(batch)
        if len(batch) < 100:
            return repositories
        page += 1


def search_count(query: str, endpoint: str = "issues") -> int | None:
    encoded = urllib.parse.urlencode({"q": query, "per_page": 1})
    try:
        result = request_json(f"{API}/search/{endpoint}?{encoded}")
    except urllib.error.HTTPError as error:
        print(f"warning: GitHub search failed ({error.code}): {query}", file=sys.stderr)
        return None
    return int(result["total_count"])


def contribution_count(login: str) -> int | None:
    if not TOKEN:
        return None

    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar { totalContributions }
        }
      }
    }
    """
    try:
        result = request_json(
            f"{API}/graphql",
            body={"query": query, "variables": {"login": login}},
        )
        return int(
            result["data"]["user"]["contributionsCollection"]
            ["contributionCalendar"]["totalContributions"]
        )
    except (KeyError, TypeError, urllib.error.HTTPError) as error:
        print(f"warning: contribution query failed: {error}", file=sys.stderr)
        return None


def main() -> None:
    if not USERNAME:
        raise SystemExit("GITHUB_USER is required")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    profile = request_json(f"{API}/users/{USERNAME}")
    login = profile["login"]
    repositories = fetch_all_repositories(login)

    languages = Counter(
        repository["language"]
        for repository in repositories
        if repository.get("language") and not repository.get("fork")
    )

    metrics = {
        "login": login,
        "name": profile.get("name") or login,
        "public_repos": profile.get("public_repos", len(repositories)),
        "total_stars": sum(repo.get("stargazers_count", 0) for repo in repositories),
        "total_forks": sum(repo.get("forks_count", 0) for repo in repositories),
        "pull_requests": search_count(f"author:{login} type:pr"),
        "issues": search_count(f"author:{login} type:issue"),
        "commits": search_count(f"author:{login}", endpoint="commits"),
        "contributions_365d": contribution_count(login),
        "followers": profile.get("followers", 0),
        "following": profile.get("following", 0),
        "top_language": languages.most_common(1)[0][0] if languages else "N/A",
        "member_since": profile["created_at"][:10],
        "profile": f"github.com/{login}",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }

    (CACHE_DIR / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    avatar_url = profile["avatar_url"]
    separator = "&" if "?" in avatar_url else "?"
    download(f"{avatar_url}{separator}s=640", CACHE_DIR / "github-avatar.jpg")

    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
