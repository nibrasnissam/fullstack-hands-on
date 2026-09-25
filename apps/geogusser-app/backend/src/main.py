import math
import os
import random
import uuid
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.locations import LOCATIONS
from src.mapillary import find_nearby_image

MAPILLARY_ACCESS_TOKEN = os.environ.get("MAPILLARY_ACCESS_TOKEN", "").strip()

ROUNDS_PER_GAME = 5
MAX_POINTS_PER_ROUND = 5000
COUNTRY_BONUS = 500
# Distance (km) beyond which score decays to ~0. Tuned so a near-perfect
# guess (<25km) scores close to the max, and guesses over ~2500km away
# score close to 0.
SCORE_DECAY_KM = 2000

app = FastAPI(title="GeoGusser API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store. Fine for a single-instance demo game.
GAMES: Dict[str, dict] = {}


class GuessIn(BaseModel):
    round_index: int
    lat: float
    lng: float


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def score_for_distance(distance_km: float) -> int:
    if distance_km <= 0.5:
        return MAX_POINTS_PER_ROUND
    raw = MAX_POINTS_PER_ROUND * math.exp(-distance_km / SCORE_DECAY_KM)
    return max(0, round(raw))


def build_round_location(loc: dict) -> dict:
    """
    Resolve a curated location into the coordinate + imagery that will
    actually be used for a round. Tries a real Mapillary panorama near the
    curated coordinate first; falls back to the static photo if no token
    is set or no coverage is found nearby.
    """
    round_loc = {
        "id": loc["id"],
        "country": loc["country"],
        "city": loc["city"],
        "lat": loc["lat"],
        "lng": loc["lng"],
        "image_id": None,
        "image_url": loc["image_url"],
    }

    if MAPILLARY_ACCESS_TOKEN:
        found = find_nearby_image(loc["lat"], loc["lng"], MAPILLARY_ACCESS_TOKEN)
        if found:
            image_id, actual_lat, actual_lng = found
            round_loc["image_id"] = image_id
            round_loc["lat"] = actual_lat
            round_loc["lng"] = actual_lng

    return round_loc


def public_round(loc: dict, round_index: int) -> dict:
    """Location data safe to send to the client BEFORE they guess."""
    return {
        "round_index": round_index,
        "image_id": loc["image_id"],
        "image_url": loc["image_url"],
        "location_id": loc["id"],
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/config")
def config():
    """Public, non-secret info the frontend needs to know how to render a
    round: whether real 360 panoramas are available, and the client token
    mapillary-js needs to display them (Mapillary client tokens are meant
    to be used from the browser, so this is safe to expose)."""
    return {
        "mapillary_enabled": bool(MAPILLARY_ACCESS_TOKEN),
        "mapillary_token": MAPILLARY_ACCESS_TOKEN or None,
    }


@app.post("/api/game/new")
def new_game():
    if len(LOCATIONS) < ROUNDS_PER_GAME:
        raise HTTPException(500, "Not enough locations configured")

    game_id = str(uuid.uuid4())
    sampled: List[dict] = random.sample(LOCATIONS, ROUNDS_PER_GAME)
    chosen: List[dict] = [build_round_location(loc) for loc in sampled]
    GAMES[game_id] = {
        "rounds": chosen,
        "current_round": 0,
        "results": [],
        "total_score": 0,
    }
    return {
        "game_id": game_id,
        "rounds_total": ROUNDS_PER_GAME,
        "round": public_round(chosen[0], 0),
    }


@app.post("/api/game/{game_id}/guess")
def submit_guess(game_id: str, guess: GuessIn):
    game = GAMES.get(game_id)
    if not game:
        raise HTTPException(404, "Game not found")

    expected_index = game["current_round"]
    if guess.round_index != expected_index:
        raise HTTPException(400, "Round mismatch - are you replaying an old round?")

    loc = game["rounds"][expected_index]
    distance_km = haversine_km(guess.lat, guess.lng, loc["lat"], loc["lng"])
    score = score_for_distance(distance_km)

    # Very rough "correct country" check: within ~600km counts as a
    # reasonable proxy without needing real reverse-geocoding/borders data.
    country_bonus = COUNTRY_BONUS if distance_km <= 600 else 0
    round_score = min(MAX_POINTS_PER_ROUND, score + country_bonus)

    result = {
        "round_index": expected_index,
        "guess_lat": guess.lat,
        "guess_lng": guess.lng,
        "actual_lat": loc["lat"],
        "actual_lng": loc["lng"],
        "actual_country": loc["country"],
        "actual_city": loc["city"],
        "distance_km": round(distance_km, 1),
        "score": round_score,
        "country_bonus": country_bonus,
    }
    game["results"].append(result)
    game["total_score"] += round_score
    game["current_round"] += 1

    is_last_round = game["current_round"] >= ROUNDS_PER_GAME
    next_round = None
    if not is_last_round:
        next_round = public_round(game["rounds"][game["current_round"]], game["current_round"])

    return {
        "result": result,
        "total_score": game["total_score"],
        "game_over": is_last_round,
        "next_round": next_round,
    }


@app.get("/api/game/{game_id}/summary")
def summary(game_id: str):
    game = GAMES.get(game_id)
    if not game:
        raise HTTPException(404, "Game not found")
    return {
        "total_score": game["total_score"],
        "rounds": game["results"],
        "max_possible": ROUNDS_PER_GAME * MAX_POINTS_PER_ROUND,
    }
