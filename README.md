# Personal Portfolio Dashboard

Cooked up a portfolio with Django and plain HTML/CSS. It pulls live GitHub and Codeforces data and even writes my bio using GROQ AI.

**Live site:** [ryokrieger.vercel.app](https://ryokrieger.vercel.app/)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2 (Python) |
| Database | PostgreSQL (Neon) |
| AI | GROQ API — `qwen/qwen3-32b` |
| Frontend | HTML + CSS |
| Charts | Chart.js |
| Icons | Font Awesome 6 |
| Static Files | WhiteNoise |
| Deployment | Vercel |

---

## Architecture & Design Patterns

### Singleton Pattern — `BioCacheEntry`
`BioCacheEntry` stores only one bio at a time. Before saving a new bio, the old one is deleted. The bio is reused for up to 24 hours before generating a new one.

### Strategy Pattern — `groq_service.py`
The bio service has two strategies:
- **Primary:** Generate a bio using the GROQ qwen/qwen3-32b API.
- **Fallback:** Return a predefined static bio if the API is unavailable.

The application calls `get_bio()` without knowing which strategy is used.

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
├── dashboard/               # The main app
│   ├── models.py            # Bio cache (singleton)
│   ├── views.py             # Handles page logic
│   ├── urls.py              # Homepage route
│   ├── admin.py             # Django admin
│   ├── migrations/          # Database migrations
│   └── services/
│       └── groq_service.py  # AI bio generator + fallback
│
├── templates/
│   ├── base.html            # Shared layout
│   └── dashboard/
│       └── index.html       # Portfolio page
│
└── static/dashboard/
    ├── css/style.css        # All the styling
    ├── js/widgets.js        # Live GitHub & CF widgets
    └── img/                 # Images & assets
```