# diplomacy_ndai_zone_server

Standalone NDAI Tinfoil server that exposes a `/negotiate` endpoint for running Diplomacy NDAI zone negotiations via an OpenAI-compatible LLM backend.

## Prerequisites

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

Add the OpenRouter API key to the .env file as "OPENROUTER_API_KEY"

```bash
# Clone the repository
git clone https://github.com/enricobottazzi/diplomacy_ndai_zone_server.git
cd diplomacy_ndai_zone_server

# Install dependencies
uv sync

# Run the server
uv run uvicorn ndai_tinfoil_server:app --host 0.0.0.0 --port 8000
```