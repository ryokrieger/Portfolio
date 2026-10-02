import logging

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com/repos"
GITHUB_TIMEOUT_SECONDS = 4

# stars_count is None (not 0) when we have never managed to fetch the repo, so
# the page can hide the star badge instead of showing a misleading "0".
DEFAULT_REPO_DATA = {"stars_count": None, "primary_language": ""}


def _as_dict(row) -> dict:
    return {"stars_count": row.stars_count, "primary_language": row.primary_language}


# ── Cache access (touches the database — call from the main thread) ────────────

def get_cached_repo(repo_full_name: str):
    """
    Returns (fresh, stale) for one repo, e.g. "ryokrieger/Baymax".

    - fresh: cached data younger than GITHUB_CACHE_TTL_SECONDS, else None.
    - stale: any cached data, however old, else None.
    """
    from dashboard.models import GitHubRepoCacheEntry

    try:
        row = GitHubRepoCacheEntry.objects.filter(repo_full_name=repo_full_name).first()
    except Exception as exc:
        logger.warning("Could not query GitHub cache for %s: %s", repo_full_name, exc)
        return None, None

    if row is None:
        return None, None
    data = _as_dict(row)
    return (data if row.is_fresh else None), data


def save_repo(repo_full_name: str, data: dict) -> None:
    from dashboard.models import GitHubRepoCacheEntry

    try:
        GitHubRepoCacheEntry.objects.update_or_create(
            repo_full_name=repo_full_name,
            defaults={
                "stars_count": data["stars_count"] or 0,
                "primary_language": data["primary_language"],
                "fetched_at": timezone.now(),
            },
        )
        logger.info("GitHub data refreshed for %s.", repo_full_name)
    except Exception as exc:
        logger.warning("Could not save GitHub cache for %s: %s", repo_full_name, exc)


# ── Network access (NO database — safe to run in a background thread) ─────────

def fetch_repo(repo_full_name: str) -> dict:
    """
    Calls the GitHub API once and returns {"stars_count", "primary_language"}.
    Raises an exception if the call fails.

    If GITHUB_TOKEN is set it is sent along, which raises GitHub's rate limit
    from 60 to 5,000 requests per hour.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ryokrieger-portfolio",
    }
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    response = requests.get(
        f"{GITHUB_API_BASE}/{repo_full_name}",
        headers=headers,
        timeout=GITHUB_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    body = response.json()
    return {
        "stars_count": body.get("stargazers_count", 0),
        "primary_language": body.get("language") or "",
    }


# ── Simple sequential versions (the page uses live_data.py instead) ────────────

def get_repo_data(repo_full_name: str) -> dict:
    """fresh cache -> live API -> stale cache -> defaults."""
    fresh, stale = get_cached_repo(repo_full_name)
    if fresh is not None:
        return fresh
    try:
        data = fetch_repo(repo_full_name)
        save_repo(repo_full_name, data)
        return data
    except Exception as exc:
        logger.warning("GitHub API call failed for %s: %s", repo_full_name, exc)
        return stale or dict(DEFAULT_REPO_DATA)


def get_repos_data(repo_full_names: list) -> dict:
    return {name: get_repo_data(name) for name in repo_full_names}