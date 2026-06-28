from django.contrib import admin
from .models import BioCacheEntry


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