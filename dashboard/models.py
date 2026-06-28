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