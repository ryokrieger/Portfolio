import logging
from datetime import datetime, timedelta, timezone as dt_timezone

import requests
from django.utils import timezone

logger = logging.getLogger(__name__)

CF_API_BASE = "https://codeforces.com/api"
HEATMAP_WEEKS = 26  # 26-week / 182-day heatmap window

DEFAULT_STATS = {
    "rating": None,
    "max_rating": None,
    "rank": "",
    "solved_count": 0,
    "rating_history": [],
    "submission_heatmap": [],
}


def _build_rating_history(contests: list) -> list:
    """
    Turns Codeforces' user.rating result into the shape the rating chart
    needs: [{"contest_name": ..., "date_label": "Jan '25", "rating": 1500}, ...]
    Formatting the label here (server-side, once per cache window) means
    widgets.js no longer has to do date math on every page load.
    """
    history = []
    for c in contests:
        dt = datetime.fromtimestamp(c.get("ratingUpdateTimeSeconds", 0), tz=dt_timezone.utc)
        history.append({
            "contest_name": c.get("contestName", ""),
            "date_label": dt.strftime("%b '%y"),
            "rating": c.get("newRating"),
        })
    return history


def _level_for_count(count: int) -> int:
    """Same 6-level bucketing V1's client-side buildHeatmap() used."""
    if count == 0:
        return 0
    if count == 1:
        return 1
    if count <= 3:
        return 2
    if count <= 5:
        return 3
    if count <= 8:
        return 4
    return 5


def _build_heatmap(submissions: list) -> list:
    """
    Turns raw Codeforces submissions into a day-by-day grid for the last
    26 weeks, aligned to the previous Sunday —
    client-side buildHeatmap() used, just computed once server-side now:
    [{"date": "YYYY-MM-DD", "count": int, "level": 0-5}, ...]
    """
    now = timezone.now()
    window_start = now - timedelta(weeks=HEATMAP_WEEKS)

    counts = {}
    for s in submissions:
        ts = datetime.fromtimestamp(s.get("creationTimeSeconds", 0), tz=dt_timezone.utc)
        if ts < window_start:
            continue
        key = ts.strftime("%Y-%m-%d")
        counts[key] = counts.get(key, 0) + 1

    # Rewind to the nearest previous Sunday, same as V1
    start_date = (window_start - timedelta(days=(window_start.isoweekday() % 7))).date()
    end_date = now.date()

    cells = []
    cursor = start_date
    while cursor <= end_date:
        key = cursor.strftime("%Y-%m-%d")
        count = counts.get(key, 0)
        cells.append({"date": key, "count": count, "level": _level_for_count(count)})
        cursor += timedelta(days=1)

    return cells


def get_codeforces_stats(handle: str = "ryokrieger") -> dict:
    """
    Returns {"rating", "max_rating", "rank", "solved_count",
    "rating_history", "submission_heatmap"} for the given CF handle.

    1. Check CodeforcesCacheEntry (singleton per handle, same pattern as
       BioCacheEntry) for a row younger than
       settings.CODEFORCES_CACHE_TTL_SECONDS. If found, return it.
    2. Otherwise call all three CF endpoints once, save the combined
       result, return it.
    3. If any call fails, fall back to a stale cached row if one exists,
       or zeroed-out defaults if not.
    """
    from dashboard.models import CodeforcesCacheEntry

    cached = CodeforcesCacheEntry.objects.filter(handle=handle).first()
    if cached and cached.is_fresh:
        logger.debug("Codeforces cache hit for %s.", handle)
        return {
            "rating": cached.rating,
            "max_rating": cached.max_rating,
            "rank": cached.rank,
            "solved_count": cached.solved_count,
            "rating_history": cached.rating_history,
            "submission_heatmap": cached.submission_heatmap,
        }

    try:
        info_res = requests.get(f"{CF_API_BASE}/user.info", params={"handles": handle}, timeout=5)
        status_res = requests.get(f"{CF_API_BASE}/user.status", params={"handle": handle, "count": 500}, timeout=5)
        rating_res = requests.get(f"{CF_API_BASE}/user.rating", params={"handle": handle}, timeout=5)

        info_res.raise_for_status()
        status_res.raise_for_status()
        rating_res.raise_for_status()

        info_data = info_res.json()
        status_data = status_res.json()
        rating_data = rating_res.json()

        if (
            info_data.get("status") != "OK"
            or status_data.get("status") != "OK"
            or rating_data.get("status") != "OK"
        ):
            raise ValueError("Codeforces API returned a non-OK status.")

        user = info_data["result"][0]
        rating = user.get("rating")
        max_rating = user.get("maxRating")
        rank = user.get("rank", "")

        submissions = status_data["result"]
        solved_count = len({
            f"{s['problem']['contestId']}-{s['problem']['index']}"
            for s in submissions
            if s.get("verdict") == "OK" and "contestId" in s.get("problem", {})
        })
        submission_heatmap = _build_heatmap(submissions)
        rating_history = _build_rating_history(rating_data["result"])

        # Singleton pattern, same as BioCacheEntry — delete old row(s), create fresh
        CodeforcesCacheEntry.objects.filter(handle=handle).delete()
        CodeforcesCacheEntry.objects.create(
            handle=handle,
            rating=rating,
            max_rating=max_rating,
            rank=rank,
            solved_count=solved_count,
            rating_history=rating_history,
            submission_heatmap=submission_heatmap,
        )
        logger.info("Codeforces data refreshed for %s.", handle)

        return {
            "rating": rating,
            "max_rating": max_rating,
            "rank": rank,
            "solved_count": solved_count,
            "rating_history": rating_history,
            "submission_heatmap": submission_heatmap,
        }

    except Exception as exc:
        logger.warning("Codeforces API call failed for %s: %s", handle, exc)
        if cached:
            return {
                "rating": cached.rating,
                "max_rating": cached.max_rating,
                "rank": cached.rank,
                "solved_count": cached.solved_count,
                "rating_history": cached.rating_history,
                "submission_heatmap": cached.submission_heatmap,
            }
        return dict(DEFAULT_STATS)