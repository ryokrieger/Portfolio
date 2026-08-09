import logging
from django.shortcuts import render
from dashboard.services.groq_service import get_bio
from dashboard.services.github_service import get_repos_data
from dashboard.services.codeforces_service import get_codeforces_stats

logger = logging.getLogger(__name__)

# ── Profile picture ────────────────────────────────────────────────────────────
PROFILE_PIC = "profile.jpg"

# ── Tagline ────────────────────────────────────────────────────────────────────
TAGLINE = "CSE undergrad · Dhaka · AI / ML Research"

# ── Languages & skills ─────────────────────────────────────────────────────────
LANGUAGES = {
    "fluent": ["Bangla", "English"],
    "working_on": ["French"],
    "programming": ["C++", "Python"],
}

# ── Social links ───────────────────────────────────────────────────────────────
SOCIAL_LINKS = [
    {
        "platform": "LinkedIn",
        "url": "https://www.linkedin.com/in/ryokrieger",
        "fa_icon": "fa-brands fa-linkedin",
        "label": "ryokrieger",
    },
    {
        "platform": "ResearchGate",
        "url": "https://www.researchgate.net/profile/Farhan-Shahid-5",
        "fa_icon": "fa-brands fa-researchgate",
        "label": "Farhan Shahid",
    },
]

# ── GitHub repositories ────────────────────────────────────────────────────────
GITHUB_USERNAME = "ryokrieger"
GITHUB_PROFILE_URL = "https://github.com/ryokrieger"
GITHUB_CHART_URL = "https://ghchart.rshah.org/ryokrieger"

GITHUB_REPOS = [
    {
        "name": "Mental-Health-Assessment",
        "description": "Machine Learning-Based Mental Health Status Classification Among Bangladeshi University Students Using Combined Psychometric Scales.",
        "url": "https://github.com/ryokrieger/Mental-Health-Assessment",
    },
    {
        "name": "Baymax",
        "description": "A Mental Health Tracking System Built for University Students.",
        "url": "https://github.com/ryokrieger/Baymax",
    },
    {
        "name": "CityConnect",
        "description": "A Community-Driven Social Platform Connecting People by Shared Interests, Location, and Local Events.",
        "url": "https://github.com/ryokrieger/CityConnect",
    },
    {
        "name": "Portfolio",
        "description": "Personal Portfolio Dashboard.",
        "url": "https://github.com/ryokrieger/Portfolio",
    },
]

# ── Codeforces ─────────────────────────────────────────────────────────────────
CODEFORCES = {
    "username": "ryokrieger",
    "profile_url": "https://codeforces.com/profile/ryokrieger",
}

# ── Spotify ────────────────────────────────────────────────────────────────────
SPOTIFY = {
    "profile_url": "https://open.spotify.com/user/31njm56gpc6j7cmilsthjrj3hwzi",
    "playlist_embed_url": "https://open.spotify.com/embed/playlist/0e3Ugs2J3MBsURVKdRst54",
    "artists": [
        {
            "name": "Adele",
            "url": "https://open.spotify.com/artist/4dpARuHxo51G3z768sgnrY",
            "image_filename": "adele.jpg",
        },
        {
            "name": "Joji",
            "url": "https://open.spotify.com/artist/3MZsBdqDrRTJihTHQrO6Dq",
            "image_filename": "joji.jpg",
        },
        {
            "name": "Panic! At The Disco",
            "url": "https://open.spotify.com/artist/20JZFwl6HVl6yg8a4H3ZqK",
            "image_filename": "panicatthedisco.jpg",
        },
        {
            "name": "mxmtoon",
            "url": "https://open.spotify.com/artist/0HthCchcL0kVLHTr113Vk1",
            "image_filename": "mxmtoon.jpg",
        },
    ],
}

# ── YouTube ────────────────────────────────────────────────────────────────────
YOUTUBE = {
    "own_channel_url": "https://www.youtube.com/@ryokrieger",
    "favourites": [
        {
            "name": "PewDiePie",
            "url": "https://www.youtube.com/@PewDiePie",
            "image_filename": "pewdiepie.jpg",
            "initials": "PD",
        },
        {
            "name": "Simone Giertz",
            "url": "https://www.youtube.com/@simonegiertz",
            "image_filename": "simone_giertz.jpg",
            "initials": "SG",
        },
        {
            "name": "Sidemen",
            "url": "https://www.youtube.com/@Sidemen",
            "image_filename": "sidemen.jpg",
            "initials": "SD",
        },
        {
            "name": "Future Canoe",
            "url": "https://www.youtube.com/@FutureCanoe",
            "image_filename": "future_canoe.jpg",
            "initials": "FC",
        },
    ],
}

# ── Letterboxd ─────────────────────────────────────────────────────────────────
LETTERBOXD = {
    "profile_url": "https://letterboxd.com/ryokrieger/",
    "films": [
        {
            "title": "Amélie",
            "year": 2001,
            "film_url": "https://letterboxd.com/film/amelie/",
            "poster_filename": "amelie.jpg",
        },
        {
            "title": "Sentimental Value",
            "year": 2025,
            "film_url": "https://letterboxd.com/film/sentimental-value-2025/",
            "poster_filename": "sentimental_value.jpg",
        },
        {
            "title": "Jojo Rabbit",
            "year": 2019,
            "film_url": "https://letterboxd.com/film/jojo-rabbit/",
            "poster_filename": "jojo_rabbit.jpg",
        },
        {
            "title": "Everything Everywhere All at Once",
            "year": 2022,
            "film_url": "https://letterboxd.com/film/everything-everywhere-all-at-once/",
            "poster_filename": "eeaao.jpg",
        },
    ],
}


# ── The view ───────────────────────────────────────────────────────────────────
def index(request):
    # ── Bio (server-rendered, cached up to 24h) ───────────
    try:
        bio = get_bio()
    except Exception as exc:
        logger.error("get_bio() raised unexpectedly: %s", exc)
        from dashboard.services.groq_service import FALLBACK_BIO
        bio = FALLBACK_BIO

    # ── GitHub repo stats (server-cached) ──────────────────────────
    try:
        repo_full_names = [f"{GITHUB_USERNAME}/{repo['name']}" for repo in GITHUB_REPOS]
        repo_stats = get_repos_data(repo_full_names)
    except Exception as exc:
        logger.error("get_repos_data() raised unexpectedly: %s", exc)
        repo_stats = {}

    github_repos = []
    for repo in GITHUB_REPOS:
        full_name = f"{GITHUB_USERNAME}/{repo['name']}"
        stats = repo_stats.get(full_name, {"stars_count": 0, "primary_language": ""})
        github_repos.append({**repo, **stats})

    # ── Codeforces stats (server-cached) ───────────────────────────
    try:
        cf_stats = get_codeforces_stats(CODEFORCES["username"])
    except Exception as exc:
        logger.error("get_codeforces_stats() raised unexpectedly: %s", exc)
        cf_stats = {
            "rating": None,
            "max_rating": None,
            "rank": "",
            "solved_count": 0,
            "rating_history": [],
            "submission_heatmap": [],
        }

    codeforces = {**CODEFORCES, **cf_stats}

    context = {
        "profile_pic": PROFILE_PIC,
        "tagline": TAGLINE,
        "languages": LANGUAGES,
        "bio": bio,
        "social_links": SOCIAL_LINKS,
        "github_repos": github_repos,
        "github_username": GITHUB_USERNAME,
        "github_profile_url": GITHUB_PROFILE_URL,
        "github_chart_url": GITHUB_CHART_URL,
        "codeforces": codeforces,
        "spotify": SPOTIFY,
        "youtube": YOUTUBE,
        "letterboxd": LETTERBOXD,
    }

    return render(request, "dashboard/index.html", context)