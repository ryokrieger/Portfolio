import logging
from django.shortcuts import render
from dashboard.services.groq_service import get_bio

logger = logging.getLogger(__name__)

# ── Profile picture ────────────────────────────────────────────────────────────
PROFILE_PIC = "profile.jpg"

# ── Tagline ────────────────────────────────────────────────────────────────────
TAGLINE = "CSE undergrad · Dhaka · AI / ML Research"

# ── Languages & skills ─────────────────────────────────────────────────────────
LANGUAGES = {
    "fluent": ["Bangla", "English"],
    "working_on": ["Dutch", "French"],
    "programming": ["C++", "Python"],
}

# ── Social links ───────────────────────────────────────────────────────────────
SOCIAL_LINKS = [
    {
        "platform": "Instagram",
        "url": "https://www.instagram.com/ryokrieger/",
        "fa_icon": "fa-brands fa-instagram",
        "label": "ryokrieger",
    },
    {
        "platform": "Twitter / X",
        "url": "https://x.com/ryokrieger",
        "fa_icon": "fa-brands fa-x-twitter",
        "label": "ryokrieger",
    },
    {
        "platform": "YouTube",
        "url": "https://www.youtube.com/@ryokrieger",
        "fa_icon": "fa-brands fa-youtube",
        "label": "ryokrieger",
    },
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
GITHUB_REPOS = [
    {
        "name": "Mental-Health-Assessment",
        "description": "MHA — Mental Health Assessment Applied to Bangladeshi University Students Using Machine Learning.",
        "url": "https://github.com/ryokrieger/Mental-Health-Assessment",
        "api_url": "https://api.github.com/repos/ryokrieger/Mental-Health-Assessment",
    },
    {
        "name": "Baymax",
        "description": "A Mental Health Tracking System Built for University Students.",
        "url": "https://github.com/ryokrieger/Baymax",
        "api_url": "https://api.github.com/repos/ryokrieger/Baymax",
    },
    {
        "name": "CityConnect",
        "description": "A Community-Driven Social Platform Connecting People by Shared Interests, Location, and Local Events.",
        "url": "https://github.com/ryokrieger/CityConnect",
        "api_url": "https://api.github.com/repos/ryokrieger/CityConnect",
    },
    {
        "name": "Portfolio",
        "description": "Personal Portfolio Dashboard.",
        "url": "https://github.com/ryokrieger/Portfolio",
        "api_url": "https://api.github.com/repos/ryokrieger/Portfolio",
    },
]

GITHUB_USERNAME = "ryokrieger"
GITHUB_PROFILE_URL = "https://github.com/ryokrieger"
GITHUB_CHART_URL = "https://ghchart.rshah.org/ryokrieger"

# ── Codeforces ─────────────────────────────────────────────────────────────────
CODEFORCES = {
    "username": "ryokrieger",
    "profile_url": "https://codeforces.com/profile/ryokrieger",
    "api_info_url": "https://codeforces.com/api/user.info?handles=ryokrieger",
    "api_status_url": "https://codeforces.com/api/user.status?handle=ryokrieger&count=500",
    "api_rating_url": "https://codeforces.com/api/user.rating?handle=ryokrieger",
}

# ── Spotify ────────────────────────────────────────────────────────────────────
SPOTIFY = {
    "profile_url": "https://open.spotify.com/user/31njm56gpc6j7cmilsthjrj3hwzi",
    "playlist_embed_url": "https://open.spotify.com/embed/playlist/0e3Ugs2J3MBsURVKdRst54",
    "artists": [
        {
            "name": "Joji",
            "url": "https://open.spotify.com/artist/3MZsBdqDrRTJihTHQrO6Dq",
            "image_filename": "joji.jpg",
        },
        {
            "name": "mxmtoon",
            "url": "https://open.spotify.com/artist/0HthCchcL0kVLHTr113Vk1",
            "image_filename": "mxmtoon.jpg",
        },
        {
            "name": "Lorde",
            "url": "https://open.spotify.com/artist/163tK9Wjr9P9DmM0AVK7lm",
            "image_filename": "lorde.jpg",
        },
        {
            "name": "Scarlet Pleasure",
            "url": "https://open.spotify.com/artist/7wrulS1dfanckBnoxxEuS6",
            "image_filename": "scarlet_pleasure.jpg",
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

# ── Goodreads ──────────────────────────────────────────────────────────────────
GOODREADS = {
    "profile_url": "https://www.goodreads.com/user/show/184240877-farhan-shahid",
    "books": [
        {
            "title": "Crime and Punishment",
            "author": "Fyodor Dostoevsky",
            "book_url": "https://www.goodreads.com/book/show/7144.Crime_and_Punishment",
            "cover_filename": "crime_punishment.jpg",
        },
        {
            "title": "1984",
            "author": "George Orwell",
            "book_url": "https://www.goodreads.com/book/show/61439040-1984",
            "cover_filename": "1984.jpg",
        },
        {
            "title": "Norwegian Wood",
            "author": "Haruki Murakami",
            "book_url": "https://www.goodreads.com/book/show/11297.Norwegian_Wood",
            "cover_filename": "norwegian_wood.jpg",
        },
        {
            "title": "The Inugami Curse",
            "author": "Seishi Yokomizo",
            "book_url": "https://www.goodreads.com/book/show/50362362-the-inugami-curse",
            "cover_filename": "inugami_curse.jpg",
        },
    ],
}

# ── The view ───────────────────────────────────────────────────────────────────
def index(request):
    try:
        bio = get_bio()
    except Exception as exc:
        logger.error("get_bio() raised unexpectedly: %s", exc)
        from dashboard.services.groq_service import FALLBACK_BIO
        bio = FALLBACK_BIO

    context = {
        "profile_pic": PROFILE_PIC,
        "tagline": TAGLINE,
        "languages": LANGUAGES,
        "bio": bio,
        "social_links": SOCIAL_LINKS,
        "github_repos": GITHUB_REPOS,
        "github_username": GITHUB_USERNAME,
        "github_profile_url": GITHUB_PROFILE_URL,
        "github_chart_url": GITHUB_CHART_URL,
        "codeforces": CODEFORCES,
        "spotify": SPOTIFY,
        "youtube": YOUTUBE,
        "letterboxd": LETTERBOXD,
        "goodreads": GOODREADS,
    }

    return render(request, "dashboard/index.html", context)