from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BioCacheEntry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("bio_text", models.TextField(help_text="The AI-generated bio paragraph.")),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        help_text="When this bio was generated. Used to check if it's expired.",
                    ),
                ),
            ],
            options={
                "verbose_name": "Bio Cache Entry",
                "verbose_name_plural": "Bio Cache Entries",
                "ordering": ["-created_at"],
            },
        ),
    ]