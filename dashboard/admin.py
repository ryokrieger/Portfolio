from django.contrib import admin
from .models import BioCacheEntry, GitHubRepoCacheEntry, CodeforcesCacheEntry


@admin.register(BioCacheEntry)
class BioCacheEntryAdmin(admin.ModelAdmin):
    """
    Makes the AI bio cache visible in the Django admin panel.
    Useful for manually clearing the cache if you want a fresh bio.
    """
    list_display = ("id", "created_at", "bio_preview")
    readonly_fields = ("created_at", "bio_text")
    ordering = ("-created_at",)

    def bio_preview(self, obj):
        """Show first 80 characters of the bio in the list view."""
        return obj.bio_text[:80] + "…" if len(obj.bio_text) > 80 else obj.bio_text
    bio_preview.short_description = "Bio preview"


@admin.register(GitHubRepoCacheEntry)
class GitHubRepoCacheEntryAdmin(admin.ModelAdmin):
    """
    Makes the cached GitHub repo stats visible in the admin panel.
    Useful for checking when each repo was last refreshed, or deleting a
    row to force a re-fetch on the next page load.
    """
    list_display = ("repo_full_name", "stars_count", "primary_language", "fetched_at", "is_fresh")
    readonly_fields = ("fetched_at",)
    ordering = ("repo_full_name",)

    def is_fresh(self, obj):
        return obj.is_fresh
    is_fresh.boolean = True
    is_fresh.short_description = "Fresh?"


@admin.register(CodeforcesCacheEntry)
class CodeforcesCacheEntryAdmin(admin.ModelAdmin):
    """
    Makes the cached Codeforces stats visible in the admin panel.
    Useful for checking when the CF data was last refreshed, or deleting
    the row to force a re-fetch on the next page load.
    """
    list_display = ("handle", "rating", "max_rating", "rank", "solved_count", "fetched_at", "is_fresh")
    readonly_fields = ("fetched_at", "rating_history", "submission_heatmap")
    ordering = ("-fetched_at",)

    def is_fresh(self, obj):
        return obj.is_fresh
    is_fresh.boolean = True
    is_fresh.short_description = "Fresh?"