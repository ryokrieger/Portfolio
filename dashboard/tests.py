import re
from unittest import mock

from django.contrib.staticfiles import finders
from django.test import TestCase, override_settings

from dashboard.services import codeforces_service, github_service, groq_service

# Plain static storage so the tests don't need `collectstatic` to have been run.
PLAIN_STATIC = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@override_settings(STORAGES=PLAIN_STATIC)
class PortfolioPageTests(TestCase):
    def test_page_still_loads_when_every_outside_service_is_down(self):
        """
        Groq, GitHub and Codeforces all fail -> the page must still return 200,
        show the built-in fallback bio, hide the unknown star counts and show
        "—" for the unknown Codeforces numbers.
        """
        down = mock.Mock(side_effect=RuntimeError("service is down"))
        with mock.patch.object(groq_service, "bio_fetch_enabled", return_value=True), \
             mock.patch.object(groq_service, "fetch_bio", down), \
             mock.patch.object(github_service, "fetch_repo", down), \
             mock.patch.object(codeforces_service, "fetch_stats", down):
            response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CSE undergrad at North South University")  # fallback bio
        self.assertNotContains(response, "repo-card__stars")                       # no fake "0 stars"
        self.assertContains(response, "—")                                         # unknown Codeforces stats

    def test_every_file_the_page_links_to_exists(self):
        """
        Every CSS, JavaScript and image file the page points at must really be
        in the project.
        """
        with mock.patch("dashboard.views.load_live_data", return_value={
            "bio": "x", "repos": {}, "codeforces": dict(codeforces_service.DEFAULT_STATS),
        }):
            html = self.client.get("/").content.decode()

        paths = set(re.findall(r'(?:src|href)="/static/([^"]+)"', html))
        self.assertIn("dashboard/js/widgets.js", paths)
        for path in paths:
            self.assertIsNotNone(finders.find(path), f"missing static file: {path}")