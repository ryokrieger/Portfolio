import logging

from django.conf import settings

logger = logging.getLogger(__name__)

# Network limit for the Groq call. Kept short so a slow AI can never make the
# whole page hang; if it's too slow we simply show the last bio we had.
GROQ_TIMEOUT_SECONDS = 8

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
    "French is next. Adele or Joji on shuffle most days."
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
- Languages: fluent in Bangla and English, aspiring to be multilingual — currently learning French
- Music: Adele, Joji, Kendrick Lamar, Panic! At The Disco
- YouTube: PewDiePie, Simone Giertz, Sidemen, FutureCanoe
- Films: Amélie, Sentimental Value, Jojo Rabbit, Everything Everywhere All at Once
- Home: Dhaka

Output only the bio paragraph. No title, no preamble, no label."""


# ── Cache access (touches the database — call from the main thread) ────────────

def get_cached_bio():
    """
    Returns (fresh_bio, stale_bio).

    - fresh_bio: the cached bio if it is younger than 24 hours, else None.
    - stale_bio: the newest cached bio regardless of age, else None
                 (used as a fallback if the AI is unreachable).
    A database problem is treated as "nothing cached", never as a crash.
    """
    from dashboard.models import BioCacheEntry

    try:
        latest = BioCacheEntry.objects.first()
    except Exception as exc:
        logger.warning("Could not query bio cache: %s", exc)
        return None, None

    if latest is None:
        return None, None
    return (latest.bio_text if latest.is_fresh else None), latest.bio_text


def save_bio(bio_text: str) -> None:
    """Replaces the cached bio with a new one (table always holds one row)."""
    from dashboard.models import BioCacheEntry

    try:
        BioCacheEntry.objects.all().delete()
        BioCacheEntry.objects.create(bio_text=bio_text)
        logger.info("Bio refreshed from GROQ and saved to cache.")
    except Exception as exc:
        logger.warning("Could not save bio to cache: %s", exc)


# ── Network access (NO database — safe to run in a background thread) ─────────

def bio_fetch_enabled() -> bool:
    """True if a GROQ API key is configured."""
    return bool(settings.GROQ_API_KEY)


def fetch_bio() -> str:
    """
    Asks GROQ to write a fresh bio and returns the text.
    Raises an exception if anything goes wrong; the caller decides the fallback.
    """
    from groq import Groq  # type: ignore

    client = Groq(api_key=settings.GROQ_API_KEY, timeout=GROQ_TIMEOUT_SECONDS, max_retries=0)

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
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
        temperature=.50,
        reasoning_effort="low",
    )

    bio_text = (response.choices[0].message.content or "").strip()
    if not bio_text:
        raise ValueError("GROQ returned an empty response.")
    return bio_text


# ── Simple one-call version (sequential; the page uses live_data.py instead) ──

def get_bio() -> str:
    """
    Returns the bio: fresh cache -> new AI bio -> stale cache -> FALLBACK_BIO.
    """
    fresh, stale = get_cached_bio()
    if fresh:
        return fresh

    if bio_fetch_enabled():
        try:
            bio_text = fetch_bio()
            save_bio(bio_text)
            return bio_text
        except Exception as exc:
            logger.error("GROQ API call failed: %s — using fallback.", exc)
    else:
        logger.warning("GROQ_API_KEY not set — using fallback bio.")

    return stale or FALLBACK_BIO