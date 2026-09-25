# GeoGusser

A GeoGuessr-style geography game, built to fit `fullstack-hands-on`'s
`apps/<your-app>/` layout: a Python/FastAPI `backend/` and a JS `frontend/`,
wired together with `docker-compose.yml`.

## What's implemented (Classic mode)

- A welcome/home screen: enter a name or **Play as Guest** (stored in
  `localStorage`, no backend account needed)
- Random-location rounds (5 per game) pulled from a curated world location
  pool (`backend/src/locations.py`)
- **Real 360° street-level panoramas** via Mapillary when
  `MAPILLARY_ACCESS_TOKEN` is set (see below) — with an automatic fallback
  to a static photo per location if no token is set or no coverage is
  found nearby
- Expandable mini-map in the corner for placing your guess
- Move your pin before confirming with **Guess**
- Reveal screen: actual location, guess-to-actual line, distance in km
- Scoring up to 5000 pts/round (distance-based decay) plus a bonus for a
  close-enough country guess
- Running score across rounds + a final summary table
- **Play Again** to instantly start a new game

Other modes from the backlog (No Move, Timed, Country Streak, multiplayer,
real accounts, leaderboards, admin tools, etc.) aren't built yet — the mode
picker on the start screen shows them as "coming soon" placeholders so the
UI has a clear place to wire them in.

## Get a free Mapillary token (for real 360° street view)

1. Create a free account at https://www.mapillary.com and open
   https://www.mapillary.com/dashboard/developers
2. Register an application and copy its **client token** (starts with
   `MLY|...`).
3. Provide it to the backend container as `MAPILLARY_ACCESS_TOKEN` — either
   export it before running compose:
   ```bash
   export MAPILLARY_ACCESS_TOKEN="MLY|xxxxxxxx"
   docker compose up --build
   ```
   or put it in a `.env` file next to `docker-compose.yml`:
   ```
   MAPILLARY_ACCESS_TOKEN=MLY|xxxxxxxx
   ```
   Without a token, the game still runs fine — it just uses the static
   fallback photos instead of live panoramas.

## Run it

```bash
cd apps/geogusser-app
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000 (see `/api/health`, `/api/config`)

The frontend calls the backend directly from the browser at
`http://localhost:8000` (set in `frontend/src/index.html` via
`window.API_BASE`) — change that if you deploy the backend somewhere else.

## API

| Method | Path                         | Purpose                              |
|--------|------------------------------|---------------------------------------|
| POST   | `/api/game/new`              | Start a game, get round 1's photo    |
| POST   | `/api/game/{id}/guess`       | Submit a guess, get score + next round |
| GET    | `/api/game/{id}/summary`     | Final per-round breakdown             |

Game state lives in memory in the backend process — good for local play,
not for multiple backend replicas (swap in Redis/a DB for that).

## How the Mapillary lookup works

`backend/src/mapillary.py` queries the Mapillary Graph API for real photos
near each curated location's coordinate, expanding the search radius
(5.5km → ~110km) until it finds coverage. When it finds one, the round's
"actual" coordinate becomes that photo's real GPS position (more accurate
than the curated city-center guess), and the frontend renders it with
`mapillary-js` — a real, pannable/zoomable 360° viewer, not a simulation.
If nothing is found, `backend/src/main.py` falls back to the static
`image_url` from `locations.py` and the frontend shows that as a flat,
drag/scroll-to-look-around photo instead.
