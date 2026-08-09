# Personal Portfolio Dashboard

Cooked up a portfolio with Django and plain HTML/CSS. It pulls GitHub and Codeforces data and writes my bio using GROQ AI.

**Live site:** [ryokrieger.vercel.app](https://ryokrieger.vercel.app/)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2 (Python) |
| Database | PostgreSQL (Neon) |
| AI | GROQ API — `openai/gpt-oss-20b` |
| Frontend | HTML + CSS |
| Charts | Chart.js |
| Icons | Font Awesome 6 |
| Static Files | WhiteNoise |
| Deployment | Vercel |

---

## Architecture & Design Patterns

### Singleton Pattern — `BioCacheEntry` & `CodeforcesCacheEntry`
Both tables hold exactly one row at a time — the old row is deleted before a new one is saved. `BioCacheEntry` reuses the same bio for up to 24 hours; `CodeforcesCacheEntry` reuses the same rating/rank/chart/heatmap data for a configurable TTL (default 1 hour) before refreshing from the Codeforces API.

### Strategy Pattern — `groq_service.py`
The bio service has two strategies:
- **Primary:** Generate a bio using the GROQ openai/gpt-oss-20b API.
- **Fallback:** Return a predefined static bio if the API is unavailable.

The application calls `get_bio()` without knowing which strategy is used.

### Server-Side API Caching — `github_service.py` & `codeforces_service.py`
GitHub repository stats (such as stars and language) and all Codeforces stats are fetched server-side and cached using `GitHubRepoCacheEntry` (one row per repository) and `CodeforcesCacheEntry`. As a result, all visitors within the cache TTL window are served the cached data without triggering additional API calls.

---

## Project Structure

```
Portfolio/
│
├── manage.py
├── vercel.json              # Deploy stuff
├── build_files.sh           # Installs deps + collects static files
├── requirements.txt         # Python packages
├── .env
├── .gitignore
│
├── portfolio_project/       # Django config lives here
│   ├── settings.py          # App settings
│   ├── urls.py              # Main routes
│   └── wsgi.py              # Vercel entry
│
├── dashboard/                    # The main app
│   ├── models.py                 # Bio / GitHub / Codeforces caches
│   ├── views.py                  # Handles page logic
│   ├── urls.py                   # Homepage route
│   ├── admin.py                  # Django admin
│   ├── migrations/               # Database migrations
│   └── services/
│       ├── groq_service.py       # AI bio generator + fallback
│       ├── github_service.py     # GitHub stats fetch + cache
│       └── codeforces_service.py # Codeforces stats fetch + cache
│
├── templates/
│   ├── base.html             # Shared layout
│   └── dashboard/
│       └── index.html        # Portfolio page
│
└── static/dashboard/
    ├── css/style.css         # All the styling
    ├── js/widgets.js         # Draws the CF rating chart & heatmap
    └── img/                  # Images & assets
```