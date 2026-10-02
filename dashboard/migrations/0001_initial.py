import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BioCacheEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bio_text', models.TextField(help_text='The AI-generated bio paragraph.')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, help_text="When this bio was generated. Used to check if it's expired.")),
            ],
            options={
                'verbose_name': 'Bio Cache Entry',
                'verbose_name_plural': 'Bio Cache Entries',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CodeforcesCacheEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('handle', models.CharField(default='ryokrieger', max_length=50)),
                ('rating', models.IntegerField(blank=True, null=True)),
                ('max_rating', models.IntegerField(blank=True, null=True)),
                ('rank', models.CharField(blank=True, default='', max_length=50)),
                ('solved_count', models.PositiveIntegerField(default=0)),
                ('rating_history', models.JSONField(blank=True, default=list, help_text='List of {contest_name, rating, date} points for the rating chart.')),
                ('submission_heatmap', models.JSONField(blank=True, default=list, help_text='26 weekly buckets of daily submission counts, for the heatmap.')),
                ('fetched_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'Codeforces Cache Entry',
                'verbose_name_plural': 'Codeforces Cache Entries',
                'ordering': ['-fetched_at'],
            },
        ),
        migrations.CreateModel(
            name='GitHubRepoCacheEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('repo_full_name', models.CharField(help_text="e.g. 'ryokrieger/Baymax'", max_length=200, unique=True)),
                ('stars_count', models.PositiveIntegerField(default=0)),
                ('primary_language', models.CharField(blank=True, default='', max_length=50)),
                ('fetched_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'GitHub Repo Cache Entry',
                'verbose_name_plural': 'GitHub Repo Cache Entries',
                'ordering': ['repo_full_name'],
            },
        ),
    ]