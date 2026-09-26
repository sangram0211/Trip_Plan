# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Avoid writing .pyc files & buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency definition
COPY pyproject.toml .python-version ./

# Install project dependencies
RUN uv pip install --system -r <(uv pip compile pyproject.toml) || pip install --no-cache-dir \
    fastapi uvicorn jinja2 langchain langchain-groq langchain-mcp-adapters \
    langgraph langgraph-checkpoint-postgres nest-asyncio "psycopg[binary]" \
    python-dotenv redis requests certifi airportsdata

# Copy project files
COPY app.py ./
COPY frontend/ ./frontend/
COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
