"""
Central configuration.

Everything that reads the environment lives here, so the rest of the
code never touches os.getenv directly.
"""

import os
from pathlib import Path

import certifi
from dotenv import load_dotenv

load_dotenv()


# Windows / corporate networks need an explicit CA bundle for outbound TLS.
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


# =========================
# Paths
# =========================

SRC_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = SRC_DIR.parent


# =========================
# API keys
# =========================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


# =========================
# LLM
# =========================

# Check the live list with GET https://api.groq.com/openai/v1/models
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


# =========================
# Prompt truncation limits
# =========================

AIRPORT_DATA_CHAR_LIMIT = int(os.getenv("AIRPORT_DATA_CHAR_LIMIT", "3000"))
AIRLINE_DATA_CHAR_LIMIT = int(os.getenv("AIRLINE_DATA_CHAR_LIMIT", "3000"))


# =========================
# Redis cache
# =========================

REDIS_URL = os.getenv("REDIS_URL") or None

# Explicit off switch. Caching also requires REDIS_URL to be set.
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() not in ("false", "0", "no") and bool(REDIS_URL)

CACHE_KEY_PREFIX = "tripplanner:"
CACHE_RECONNECT_SECONDS = int(os.getenv("CACHE_RECONNECT_SECONDS", "60"))

# TTLs in seconds for each kind of cached data
CACHE_TTL_AIRPORTS = int(os.getenv("CACHE_TTL_AIRPORTS", str(7 * 24 * 3600)))   # 1 week
CACHE_TTL_AIRLINES = int(os.getenv("CACHE_TTL_AIRLINES", str(7 * 24 * 3600)))   # 1 week
CACHE_TTL_WEATHER  = int(os.getenv("CACHE_TTL_WEATHER",  str(30 * 60)))         # 30 min
CACHE_TTL_FORECAST = int(os.getenv("CACHE_TTL_FORECAST", str(3 * 3600)))        # 3 hours
CACHE_TTL_HOTELS   = int(os.getenv("CACHE_TTL_HOTELS",   str(6 * 3600)))        # 6 hours


# =========================
# Web / cookie settings
# =========================

CORS_ORIGINS_RAW = os.getenv("CORS_ORIGINS", "")
CORS_ORIGINS = [o.strip() for o in CORS_ORIGINS_RAW.split(",") if o.strip()]

COOKIE_SECURE   = os.getenv("COOKIE_SECURE",   "false").lower() in ("true", "1", "yes")
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")


def normalize_database_url(url: str) -> str:
    """Convert postgres:// to postgresql:// which psycopg3 requires."""
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url
