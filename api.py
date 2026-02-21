"""
FastAPI app for CFL Player Identification.
Exposes the same player-identification flow as the Streamlit app via REST.

Usage:
    uv run uvicorn api:app --reload --port 8000
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from main import (
    download_image,
    load_player_data,
    filter_high_confidence_players,
    verify_players_in_database,
)
from utils import process_player_identification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# --- Request / Response models ---


class IdentifyPlayersRequest(BaseModel):
    """Request body for POST /identify-players."""

    image_url: str = Field(..., min_length=1, description="URL of the image to analyze")


class PlayerItem(BaseModel):
    """A single identified player."""

    player_name: str
    player_number: str
    player_team: str


class TelemetryAgent(BaseModel):
    """Token usage for one agent."""

    input_tokens: int = 0
    output_tokens: int = 0


class TelemetryBody(BaseModel):
    """Token usage breakdown."""

    agent_1: TelemetryAgent = Field(default_factory=TelemetryAgent)
    agent_2: TelemetryAgent = Field(default_factory=TelemetryAgent)
    total: TelemetryAgent = Field(default_factory=TelemetryAgent)


class IdentifyPlayersResponse(BaseModel):
    """Success response for POST /identify-players."""

    image_url: str
    players: list[PlayerItem]
    telemetry: TelemetryBody


def _cleanup_temp_image(image_path: str | None) -> None:
    """Remove temporary downloaded image."""
    if not image_path:
        return
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            logger.debug("Cleaned up temporary image: %s", image_path)
    except OSError as e:
        logger.warning("Failed to cleanup temporary image %s: %s", image_path, e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure player DB is loadable. No shutdown work."""
    player_data = load_player_data()
    if not player_data:
        logger.warning("Player database (cfl_players.json) not loaded at startup")
    else:
        logger.info("Player database loaded for %s teams", len(player_data))
    yield


app = FastAPI(
    title="CFL Player Identification API",
    description="Identify CFL players from an image URL using AI (Bedrock + SerpAPI).",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    """Health check. Returns 200; optionally verifies player DB is loadable."""
    player_data = load_player_data()
    if not player_data:
        raise HTTPException(
            status_code=503,
            detail="Player database (cfl_players.json) not available",
        )
    return {"status": "ok", "teams_loaded": len(player_data)}


@app.post("/identify-players", response_model=IdentifyPlayersResponse)
def identify_players_endpoint(body: IdentifyPlayersRequest):
    """
    Identify CFL players in the image at the given URL.
    Runs the same pipeline as the Streamlit app: download → AI (Agent 1 + 2) → filter → verify.
    """
    image_url = body.image_url.strip()
    if not image_url:
        raise HTTPException(
            status_code=400,
            detail="image_url must be a non-empty string",
        )

    logger.info("Identify players request for image_url=%s", image_url)

    image_path = download_image(image_url)
    if not image_path:
        _cleanup_temp_image(image_path)
        raise HTTPException(
            status_code=502,
            detail="Failed to download image from URL",
        )

    try:
        player_data = load_player_data()
        if not player_data:
            raise HTTPException(
                status_code=503,
                detail="Player database (cfl_players.json) not available",
            )

        result, telemetry = process_player_identification(image_path)
        filtered_players = filter_high_confidence_players(result)
        verified_players = verify_players_in_database(filtered_players, player_data)

        players_out = [
            PlayerItem(
                player_name=p.get("player_name", "Unknown"),
                player_number=p.get("player_number", "?"),
                player_team=p.get("player_team", "Unknown"),
            )
            for p in verified_players
        ]

        telemetry_out = TelemetryBody(
            agent_1=TelemetryAgent(
                input_tokens=telemetry.get("agent_1", {}).get("input_tokens", 0),
                output_tokens=telemetry.get("agent_1", {}).get("output_tokens", 0),
            ),
            agent_2=TelemetryAgent(
                input_tokens=telemetry.get("agent_2", {}).get("input_tokens", 0),
                output_tokens=telemetry.get("agent_2", {}).get("output_tokens", 0),
            ),
            total=TelemetryAgent(
                input_tokens=telemetry.get("total", {}).get("input_tokens", 0),
                output_tokens=telemetry.get("total", {}).get("output_tokens", 0),
            ),
        )

        return IdentifyPlayersResponse(
            image_url=image_url,
            players=players_out,
            telemetry=telemetry_out,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Identify players failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Player identification failed: {str(e)}",
        )
    finally:
        _cleanup_temp_image(image_path)
