import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import requests
from django.utils import timezone

logger = logging.getLogger(__name__)

CF_API_BASE = "https://codeforces.com/api"
HEATMAP_WEEKS = 26  # the heatmap is exactly 26 columns (weeks) wide

# Network limits (seconds). user.status returns the whole submission history,
# so it is allowed a little longer than the other two.
CF_INFO_TIMEOUT = 5
CF_RATING_TIMEOUT = 5
CF_STATUS_TIMEOUT = 7

# None (not 0) means "we couldn't get this", so the page shows "—".
DEFAULT_STATS = {
    "rating": None,
    "max_rating": None,
    "rank": "",
    "solved_count": None,
    "rating_history": [],
    "submission_heatmap": [],
}


def _local_tz():
    """The site's timezone (Asia/Dhaka, from settings.TIME_ZONE)."""
    return timezone.get_current_timezone()


def _build_rating_history(contests: list) -> list:
    """
    Turns Codeforces' user.rating result into the shape the rating chart
    needs: [{"contest_name": ..., "date_label": "Jan '25", "rating": 1500}, ...]
    """
    tz = _local_tz()
    history = []
    for c in contests:
        dt = datetime.fromtimestamp(c.get("ratingUpdateTimeSeconds", 0), tz=tz)
        history.append({
            "contest_name": c.get("contestName", ""),
            "date_label": dt.strftime("%b '%y"),
            "rating": c.get("newRating"),
        })
    return history


def _level_for_count(count: int) -> int:
    """Colour bucket 0-5 for a day's submission count."""
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


def _build_heatmap(submissions: list, today=None) -> list:
    """
    Turns raw Codeforces submissions into a day-by-day grid:
    [{"date": "YYYY-MM-DD", "count": int, "level": 0-5}, ...]

    The grid is exactly HEATMAP_WEEKS (26) columns wide, Sunday to Saturday
    from top to bottom. It starts on the Sunday 25 weeks before this week's
    Sunday and ends today, so the last column may be only partly filled.
    Days are counted in the site's own timezone.
    """
    tz = _local_tz()
    if today is None:
        today = timezone.localtime(timezone.now(), tz).date()

    this_sunday = today - timedelta(days=today.isoweekday() % 7)
    start_date = this_sunday - timedelta(weeks=HEATMAP_WEEKS - 1)

    counts = {}
    for s in submissions:
        day = datetime.fromtimestamp(s.get("creationTimeSeconds", 0), tz=tz).date()
        if day < start_date or day > today:
            continue
        key = day.strftime("%Y-%m-%d")
        counts[key] = counts.get(key, 0) + 1

    cells = []
    cursor = start_date
    while cursor <= today:
        key = cursor.strftime("%Y-%m-%d")
        count = counts.get(key, 0)
        cells.append({"date": key, "count": count, "level": _level_for_count(count)})
        cursor += timedelta(days=1)

    return cells


def _row_as_dict(row) -> dict:
    return {
        "rating": row.rating,
        "max_rating": row.max_rating,
        "rank": row.rank,
        "solved_count": row.solved_count,
        "rating_history": row.rating_history,
        "submission_heatmap": row.submission_heatmap,
    }


# ── Cache access (touches the database — call from the main thread) ────────────

def get_cached_stats(handle: str):
    """
    Returns (fresh, stale) Codeforces stats for a handle.

    - fresh: cached data younger than CODEFORCES_CACHE_TTL_SECONDS, else None.
    - stale: any cached data, however old, else None.
    """
    from dashboard.models import CodeforcesCacheEntry

    try:
        row = CodeforcesCacheEntry.objects.filter(handle=handle).first()
    except Exception as exc:
        logger.warning("Could not query Codeforces cache for %s: %s", handle, exc)
        return None, None

    if row is None:
        return None, None
    data = _row_as_dict(row)
    return (data if row.is_fresh else None), data


def save_stats(handle: str, stats: dict) -> None:
    """Replaces the cached row for this handle (singleton per handle)."""
    from dashboard.models import CodeforcesCacheEntry

    try:
        CodeforcesCacheEntry.objects.filter(handle=handle).delete()
        CodeforcesCacheEntry.objects.create(handle=handle, **stats)
        logger.info("Codeforces data refreshed for %s.", handle)
    except Exception as exc:
        logger.warning("Could not save Codeforces cache for %s: %s", handle, exc)


# ── Network access (NO database — safe to run in a background thread) ─────────

def _get_json(path: str, params: dict, timeout: int) -> dict:
    response = requests.get(f"{CF_API_BASE}/{path}", params=params, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "OK":
        raise ValueError(f"Codeforces {path} returned status {data.get('status')!r}.")
    return data


def fetch_stats(handle: str) -> dict:
    """
    Calls the three Codeforces endpoints AT THE SAME TIME and returns the
    combined stats. Raises an exception if any of them fails.

    user.status is called WITHOUT a "count" limit, so it returns the entire
    submission history. That makes "problems solved" a true all-time number
    (V1 only looked at the latest 500 submissions).
    """
    with ThreadPoolExecutor(max_workers=3) as pool:
        info_f = pool.submit(_get_json, "user.info", {"handles": handle}, CF_INFO_TIMEOUT)
        status_f = pool.submit(_get_json, "user.status", {"handle": handle}, CF_STATUS_TIMEOUT)
        rating_f = pool.submit(_get_json, "user.rating", {"handle": handle}, CF_RATING_TIMEOUT)
        info_data = info_f.result()
        status_data = status_f.result()
        rating_data = rating_f.result()

    user = info_data["result"][0]
    submissions = status_data["result"]

    solved_count = len({
        f"{s['problem']['contestId']}-{s['problem']['index']}"
        for s in submissions
        if s.get("verdict") == "OK" and "contestId" in s.get("problem", {})
    })

    return {
        "rating": user.get("rating"),
        "max_rating": user.get("maxRating"),
        "rank": user.get("rank", ""),
        "solved_count": solved_count,
        "rating_history": _build_rating_history(rating_data["result"]),
        "submission_heatmap": _build_heatmap(submissions),
    }


# ── Simple sequential version (the page uses live_data.py instead) ─────────────

def get_codeforces_stats(handle: str = "ryokrieger") -> dict:
    """fresh cache -> live API -> stale cache -> defaults."""
    fresh, stale = get_cached_stats(handle)
    if fresh is not None:
        return fresh
    try:
        stats = fetch_stats(handle)
        save_stats(handle, stats)
        return stats
    except Exception as exc:
        logger.warning("Codeforces API call failed for %s: %s", handle, exc)
        return stale or dict(DEFAULT_STATS)