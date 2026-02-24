"""
Standalone NDAI Tinfoil server.
"""

import os
import logging
import time
import traceback
from collections import defaultdict
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from diplomacy.utils.export import from_saved_game_format
import ai_diplomacy
from ai_diplomacy.clients import OpenAIClient
from ai_diplomacy.game_history import GameHistory, Phase, Message
from ai_diplomacy.ndai_server import run_ndai_negotiations

load_dotenv()
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("ndai_tinfoil_server")

NDAI_LLM_BASE_URL = "https://openrouter.ai/api/v1"
NDAI_LLM_API_KEY = os.getenv("OPENROUTER_API_KEY")
NDAI_LLM_MODEL = "meta-llama/llama-3.3-70b-instruct"
DEFAULT_PROMPTS_DIR = os.path.join(os.path.dirname(ai_diplomacy.__file__), "prompts_simple")

app = FastAPI(title="NDAI Tinfoil Server")


@app.exception_handler(Exception)
async def _global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    logger.error("Unhandled exception:\n%s", "".join(tb))
    return JSONResponse(status_code=500, content={"detail": str(exc)})


# ---------------------------------------------------------------------------
# Lightweight stand-in for DiplomacyAgent — only the fields ndai_server reads
# ---------------------------------------------------------------------------
class _AgentStub:
    def __init__(self, client, goals, relationships, diary):
        self.client = client
        self.goals = goals
        self.relationships = relationships
        self._diary = diary

    def format_private_diary_for_prompt(self):
        return self._diary


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------
class AgentState(BaseModel):
    goals: list[str] = []
    relationships: dict[str, str] = {}
    diary: str = ""


class NegotiateRequest(BaseModel):
    saved_game: dict
    game_history: dict
    agent_state: dict[str, AgentState]
    max_rounds: int = 3
    model_name: Optional[str] = None
    prompts_dir: Optional[str] = None
    log_file_path: str = "/tmp/ndai_tinfoil.csv"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _rebuild_game_history(data: dict) -> GameHistory:
    gh = GameHistory()
    for p in data.get("phases", []):
        gh.phases.append(Phase(
            name=p["name"],
            plans=p.get("plans", {}),
            messages=[Message(**m) for m in p.get("messages", [])],
            submitted_orders_by_power=p.get("submitted_orders_by_power", {}),
            orders_by_power=defaultdict(list, p.get("orders_by_power", {})),
            results_by_power=defaultdict(list, p.get("results_by_power", {})),
            phase_summaries=p.get("phase_summaries", {}),
            experience_updates=p.get("experience_updates", {}),
        ))
    return gh


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@app.post("/negotiate")
async def negotiate(req: NegotiateRequest):
    t0 = time.time()
    logger.info("=== /negotiate request received ===")
    logger.info("  powers in agent_state: %s", list(req.agent_state.keys()))
    logger.info("  max_rounds=%d  model_name=%s", req.max_rounds, req.model_name)
    logger.info("  game_history phases: %d", len(req.game_history.get("phases", [])))

    game = from_saved_game_format(req.saved_game)
    logger.info("  Game reconstructed – phase: %s, powers: %s",
                game.current_short_phase, list(game.powers.keys()))

    model = req.model_name or NDAI_LLM_MODEL
    logger.info("  Using model: %s  base_url: %s", model, NDAI_LLM_BASE_URL)

    client = OpenAIClient(
        model_name=model,
        prompts_dir=req.prompts_dir or DEFAULT_PROMPTS_DIR,
        base_url=NDAI_LLM_BASE_URL,
        api_key=NDAI_LLM_API_KEY,
    )

    agents = {
        power: _AgentStub(client, s.goals, s.relationships, s.diary)
        for power, s in req.agent_state.items()
    }

    game_history = _rebuild_game_history(req.game_history)
    logger.info("  GameHistory rebuilt – %d phases", len(game_history.phases))

    error_stats: dict = {model: {"conversation_errors": 0}}

    logger.info("  Calling run_ndai_negotiations ...")
    agreed = await run_ndai_negotiations(
        game=game,
        agents=agents,
        game_history=game_history,
        model_error_stats=error_stats,
        log_file_path=req.log_file_path,
        max_rounds=req.max_rounds,
    )

    elapsed = time.time() - t0
    logger.info("  run_ndai_negotiations finished in %.1fs", elapsed)
    logger.info("  agreed_statements: %d", len(agreed))
    for k, v in agreed.items():
        logger.info("    %s -> %s: %s", k[0], k[1], v[:120])
    logger.info("  error_stats: %s", error_stats)

    return {
        "agreed_statements": {f"{k[0]}|{k[1]}": v for k, v in agreed.items()},
        "model_error_stats": error_stats,
    }
