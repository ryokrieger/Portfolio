from django.conf import settings
from django.db import models
from django.utils import timezone


class BioCacheEntry(models.Model):
    """
    Stores the AI-generated bio text in the database.

    Why? Because calling the GROQ API on every single page load would be
    slow and wasteful. Instead, we call it once, save the result here,
    and reuse it for 24 hours. After 24 hours, we ask GROQ for a fresh one.

    This table will almost always have just one row.
    """

    bio_text = models.TextField(
        help_text="The AI-generated bio paragraph."
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this bio was generated. Used to check if it's expired."
    )

    class Meta:
        verbose_name = "Bio Cache Entry"
        verbose_name_plural = "Bio Cache Entries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Bio cached at {self.created_at.strftime('%Y-%m-%d %H:%M')} UTC"

    @property
    def is_fresh(self):
        """
        Returns True if this bio was generated less than 24 hours ago.
        Once it returns False, the next page load will ask GROQ for a new one.
        """
        age = timezone.now() - self.created_at
        return age.total_seconds() < 86_400  # 86,400 seconds = 24 hours


class GitHubRepoCacheEntry(models.Model):
    """
    Caches star count + primary language for one GitHub repo.

    The server fetches it at most once per GITHUB_CACHE_TTL_SECONDS and
    every visitor gets the same cached row.

    One row per repo (not a singleton like BioCacheEntry) so each repo's
    staleness is tracked independently.
    """

    repo_full_name = models.CharField(
        max_length=200,
        unique=True,
        help_text="e.g. 'ryokrieger/Baymax'"
    )
    stars_count = models.PositiveIntegerField(default=0)
    primary_language = models.CharField(max_length=50, blank=True, default="")
    fetched_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "GitHub Repo Cache Entry"
        verbose_name_plural = "GitHub Repo Cache Entries"
        ordering = ["repo_full_name"]

    def __str__(self):
        return f"{self.repo_full_name} (cached {self.fetched_at.strftime('%Y-%m-%d %H:%M')} UTC)"

    @property
    def is_fresh(self):
        """
        Returns True if this repo's data was fetched less than
        GITHUB_CACHE_TTL_SECONDS ago.
        """
        age = timezone.now() - self.fetched_at
        return age.total_seconds() < settings.GITHUB_CACHE_TTL_SECONDS


class CodeforcesCacheEntry(models.Model):
    """
    Caches Codeforces stats for the site's one tracked handle: rating,
    max rating, rank, solved-problem count, rating history (for the chart),
    and the submission heatmap.

    Singleton-style, same reasoning as BioCacheEntry: there's only one CF
    handle this site tracks, so one row is enough. One cached row refreshed
    at most once per CODEFORCES_CACHE_TTL_SECONDS.
    """

    handle = models.CharField(max_length=50, default="ryokrieger")
    rating = models.IntegerField(null=True, blank=True)
    max_rating = models.IntegerField(null=True, blank=True)
    rank = models.CharField(max_length=50, blank=True, default="")
    solved_count = models.PositiveIntegerField(default=0)
    rating_history = models.JSONField(
        default=list,
        blank=True,
        help_text="List of {contest_name, rating, date} points for the rating chart."
    )
    submission_heatmap = models.JSONField(
        default=list,
        blank=True,
        help_text="26 weekly buckets of daily submission counts, for the heatmap."
    )
    fetched_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Codeforces Cache Entry"
        verbose_name_plural = "Codeforces Cache Entries"
        ordering = ["-fetched_at"]

    def __str__(self):
        return f"CF cache for {self.handle} ({self.fetched_at.strftime('%Y-%m-%d %H:%M')} UTC)"

    @property
    def is_fresh(self):
        """
        Returns True if this row was fetched less than
        CODEFORCES_CACHE_TTL_SECONDS ago.
        """
        age = timezone.now() - self.fetched_at
        return age.total_seconds() < settings.CODEFORCES_CACHE_TTL_SECONDS