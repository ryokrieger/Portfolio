"""
Loads everything the page needs from outside services — the AI bio, the four
GitHub repos and the Codeforces stats — as fast as possible.

How it works (three steps):

1. CHECK THE CACHE. In the main thread we read the database and see what is
   still fresh. Fresh data needs no network call at all.
2. FETCH WHAT'S MISSING, ALL AT ONCE. Anything stale is fetched in background
   threads *in parallel*, so the wait is roughly the slowest single call
   instead of all of them added together. The whole step is capped at
   TOTAL_TIMEOUT_SECONDS; whatever hasn't answered by then is skipped.
3. SAVE + FALL BACK. Successful results are written to the cache in the main
   thread (database connections are per-thread, so writes stay here).
   Anything that failed falls back to the last cached copy, then to a default.

The page therefore always renders, even if every outside service is down.
"""
import logging
from concurrent.futures import ThreadPoolExecutor, wait

from dashboard.services import codeforces_service, github_service, groq_service

logger = logging.getLogger(__name__)

# Maximum time (seconds) a visitor can wait for fresh outside data. Kept under
# Vercel's function time limit so a slow API can never take the page down.
TOTAL_TIMEOUT_SECONDS = 9


def load_live_data(repo_full_names: list, codeforces_handle: str) -> dict:
    """
    Returns {"bio": str, "repos": {full_name: {...}}, "codeforces": {...}}.
    Never raises because of a network or cache problem.
    """
    # ── 1. Cache check (main thread) ────────────────────────────────────────
    bio_fresh, bio_stale = groq_service.get_cached_bio()
    repo_cache = {name: github_service.get_cached_repo(name) for name in repo_full_names}
    cf_fresh, cf_stale = codeforces_service.get_cached_stats(codeforces_handle)

    # ── 2. Fetch whatever is stale, in parallel ─────────────────────────────
    jobs = {}
    pool = ThreadPoolExecutor(max_workers=8)
    try:
        if bio_fresh is None and groq_service.bio_fetch_enabled():
            jobs[("bio", None)] = pool.submit(groq_service.fetch_bio)

        for name in repo_full_names:
            if repo_cache[name][0] is None:
                jobs[("repo", name)] = pool.submit(github_service.fetch_repo, name)

        if cf_fresh is None:
            jobs[("cf", None)] = pool.submit(codeforces_service.fetch_stats, codeforces_handle)

        if jobs:
            wait(list(jobs.values()), timeout=TOTAL_TIMEOUT_SECONDS)
    finally:
        # Don't wait for stragglers; every request inside has its own timeout.
        pool.shutdown(wait=False, cancel_futures=True)

    def result_of(key):
        """The job's result, or None if it failed / didn't finish in time."""
        future = jobs.get(key)
        if future is None:
            return None
        if not future.done():
            logger.warning("Timed out waiting for %s.", key)
            return None
        try:
            return future.result()
        except Exception as exc:
            logger.warning("Fetching %s failed: %s", key, exc)
            return None

    # ── 3. Save new results, fall back where needed (main thread) ──────────
    # Bio: fresh cache -> new AI bio -> old cached bio -> built-in fallback
    bio = bio_fresh
    if bio is None:
        new_bio = result_of(("bio", None))
        if new_bio:
            groq_service.save_bio(new_bio)
            bio = new_bio
        else:
            bio = bio_stale or groq_service.FALLBACK_BIO

    # Repos: fresh cache -> new data -> old cached data -> "unknown"
    repos = {}
    for name in repo_full_names:
        fresh, stale = repo_cache[name]
        data = fresh
        if data is None:
            new_data = result_of(("repo", name))
            if new_data is not None:
                github_service.save_repo(name, new_data)
                data = new_data
            else:
                data = stale or dict(github_service.DEFAULT_REPO_DATA)
        repos[name] = data

    # Codeforces: fresh cache -> new data -> old cached data -> "unknown"
    cf = cf_fresh
    if cf is None:
        new_cf = result_of(("cf", None))
        if new_cf is not None:
            codeforces_service.save_stats(codeforces_handle, new_cf)
            cf = new_cf
        else:
            cf = cf_stale or dict(codeforces_service.DEFAULT_STATS)

    return {"bio": bio, "repos": repos, "codeforces": cf}