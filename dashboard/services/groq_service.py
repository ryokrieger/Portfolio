import logging

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# ── Fallback bio ───────────────────────────────────────────────────────────────
# Used when GROQ is unavailable or the API key isn't set.

FALLBACK_BIO = (
    "I'm Farhan, a CSE undergrad at North South University in Dhaka. "
    "Most of what I care about sits at the edge of AI and people — "
    "two of my projects apply machine learning to mental health screening "
    "for university students, one is a community platform built around "
    "shared interests and local life, and one is this portfolio itself. "
    "I'm working toward AI/ML research, picking up Codeforces "
    "on the side to sharpen how I think. "
    "I speak Bangla and English, and I'm aspiring to be multilingual — "
    "Dutch and French are next. Joji or Scarlet Pleasure on shuffle, "
    "Dostoevsky on the nightstand."
)

# ── GROQ prompt ────────────────────────────────────────────────────────────────
# This is the instruction we send to the model.
# It tells the model exactly what tone, length, and content to use.

BIO_PROMPT = """Write an 80–100 word personal bio for Farhan Shahid (handle: ryokrieger), a CSE undergraduate at North South University in Dhaka, Bangladesh.

Tone — this is the most important part:
- First person, sounds like a real person wrote it, not a generator
- Warm, understated, a little introspective — NOT corporate, NOT a list, NOT over-the-top
- No forced metaphors. No "symphony of creativity." No "harmony of contrasts." Just honest, clean sentences.
- Specific details earn their place. Vague gestures don't.

Facts to weave in naturally (do NOT list them — blend them):
- His main ambition: AI/ML research
- His four GitHub projects:
  1. Mental Health Assessment — applies machine learning to screen for mental health conditions among Bangladeshi university students
  2. Baymax — a mental health tracking system for university students
  3. CityConnect — a community-driven social platform that connects people by shared interests, location, and local events
  4. Portfolio — a personal portfolio dashboard
- He is building problem-solving skills through Codeforces — this is a discipline he is developing, not his identity
- Languages: fluent in Bangla and English, aspiring to be multilingual — currently learning Dutch and French
- Music: Joji, mxmtoon, Lorde, Scarlet Pleasure
- YouTube: PewDiePie, Simone Giertz, Sidemen, FutureCanoe
- Films: Amélie, Sentimental Value, Jojo Rabbit, Everything Everywhere All at Once
- Books: Crime and Punishment, 1984, Norwegian Wood, The Inugami Curse
- Home: Dhaka

Output only the bio paragraph. No title, no preamble, no label."""


def get_bio() -> str:
    """
    Returns the AI-generated bio string.

    First checks the database for a cached bio younger than 24 hours.
    If none exists (or the cached one is stale), calls GROQ for a new one.
    Falls back to FALLBACK_BIO if anything goes wrong.
    """
    # Import here to avoid circular imports at module load time
    from dashboard.models import BioCacheEntry

    # ── Step 1: Try to return a fresh cached bio ───────────────────────────────
    try:
        latest = BioCacheEntry.objects.first()
        if latest and latest.is_fresh:
            logger.debug("Bio cache hit — returning cached bio.")
            return latest.bio_text
    except Exception as exc:
        logger.warning("Could not query bio cache: %s", exc)
        return FALLBACK_BIO

    # ── Step 2: Call GROQ for a fresh bio ─────────────────────────────────────
    api_key = settings.GROQ_API_KEY
    if not api_key:
        logger.warning("GROQ_API_KEY not set — using fallback bio.")
        return FALLBACK_BIO

    try:
        from groq import Groq  # type: ignore

        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a creative writer helping a young engineer write "
                        "a personal bio for his portfolio website. Follow the user's "
                        "instructions exactly regarding tone, length, and content."
                    ),
                },
                {
                    "role": "user",
                    "content": BIO_PROMPT,
                },
            ],
            max_tokens=200,
            temperature=0.85,
        )

        bio_text = response.choices[0].message.content.strip()

        if not bio_text:
            raise ValueError("GROQ returned an empty response.")

        # ── Step 3: Save to database, delete old entries ─────────────────────
        BioCacheEntry.objects.all().delete()  # keep the table clean (1 row only)
        BioCacheEntry.objects.create(bio_text=bio_text)
        logger.info("Bio refreshed from GROQ and saved to cache.")

        return bio_text

    except Exception as exc:
        logger.error("GROQ API call failed: %s — using fallback bio.", exc)
        return FALLBACK_BIO