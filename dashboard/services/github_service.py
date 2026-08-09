import logging

import requests
from django.utils import timezone

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com/repos"

DEFAULT_REPO_DATA = {"stars_count": 0, "primary_language": ""}


def get_repo_data(repo_full_name: str) -> dict:
    """
    Returns {"stars_count": int, "primary_language": str} for one repo,
    e.g. get_repo_data("ryokrieger/Baymax").

    1. Check GitHubRepoCacheEntry for a row younger than
       settings.GITHUB_CACHE_TTL_SECONDS. If found, return it — no API call.
    2. Otherwise call the GitHub API once, save the result, return it.
    3. If the API call fails, fall back to a stale cached row if one
       exists (better than nothing), or zeroed-out defaults if not.
    """
    from dashboard.models import GitHubRepoCacheEntry

    cached = GitHubRepoCacheEntry.objects.filter(repo_full_name=repo_full_name).first()
    if cached and cached.is_fresh:
        logger.debug("GitHub cache hit for %s.", repo_full_name)
        return {"stars_count": cached.stars_count, "primary_language": cached.primary_language}

    try:
        response = requests.get(
            f"{GITHUB_API_BASE}/{repo_full_name}",
            headers={"Accept": "application/vnd.github+json"},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()

        stars_count = data.get("stargazers_count", 0)
        primary_language = data.get("language") or ""

        GitHubRepoCacheEntry.objects.update_or_create(
            repo_full_name=repo_full_name,
            defaults={
                "stars_count": stars_count,
                "primary_language": primary_language,
                "fetched_at": timezone.now(),
            },
        )
        logger.info("GitHub data refreshed for %s.", repo_full_name)
        return {"stars_count": stars_count, "primary_language": primary_language}

    except Exception as exc:
        logger.warning("GitHub API call failed for %s: %s", repo_full_name, exc)
        if cached:
            return {"stars_count": cached.stars_count, "primary_language": cached.primary_language}
        return dict(DEFAULT_REPO_DATA)


def get_repos_data(repo_full_names: list) -> dict:
    """
    Convenience wrapper for the view: returns
    {repo_full_name: {"stars_count": ..., "primary_language": ...}, ...}
    for a list of repos, e.g. the 4 repos shown on the page.
    """
    return {name: get_repo_data(name) for name in repo_full_names}