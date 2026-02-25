FROM python:3.13-slim

WORKDIR /app

# Git is required for the ai-diplomacy git dependency
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY ndai_tinfoil_server.py config.py models.py ./

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "ndai_tinfoil_server:app", "--host", "0.0.0.0", "--port", "8000"]
