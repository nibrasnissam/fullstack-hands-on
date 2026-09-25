const API = window.API_BASE;
const NAME_KEY = "geogusser_player_name";

const screens = {
  welcome: document.getElementById("screen-welcome"),
  start: document.getElementById("screen-start"),
  game: document.getElementById("screen-game"),
  result: document.getElementById("screen-result"),
  final: document.getElementById("screen-final"),
};

function showScreen(name) {
  Object.values(screens).forEach((s) => s.classList.remove("active"));
  screens[name].classList.add("active");
}

// ---------------- State ----------------
let gameId = null;
let currentRoundIndex = 0;
let totalScore = 0;
let pendingGuess = null; // {lat, lng}
let smallMap, smallMarker;
let resultMap;
let playerName = "";
let mapillaryEnabled = false;
let mapillaryToken = null;
let panoViewer = null;

// ---------------- Config (fetched once) ----------------
async function loadConfig() {
  try {
    const res = await fetch(`${API}/api/config`);
    const data = await res.json();
    mapillaryEnabled = !!data.mapillary_enabled;
    mapillaryToken = data.mapillary_token;
  } catch (e) {
    mapillaryEnabled = false;
    console.warn("Could not load config, falling back to static photos.", e);
  }
}

// ---------------- Welcome / Home screen ----------------
function initWelcome() {
  const saved = localStorage.getItem(NAME_KEY);
  const input = document.getElementById("player-name");
  const note = document.getElementById("welcome-note");
  if (saved) {
    input.value = saved;
    note.textContent = `Welcome back, ${saved}!`;
  }
}

function goToModeSelect(name) {
  playerName = name || "Guest";
  localStorage.setItem(NAME_KEY, playerName);
  document.getElementById("greeting-name").textContent = playerName;
  showScreen("start");
}

document.getElementById("btn-continue").addEventListener("click", () => {
  const name = document.getElementById("player-name").value.trim();
  goToModeSelect(name);
});

document.getElementById("btn-guest").addEventListener("click", () => {
  document.getElementById("player-name").value = "";
  goToModeSelect("Guest");
});

document.getElementById("btn-change-name").addEventListener("click", () => {
  showScreen("welcome");
});

// ---------------- Boot ----------------
initWelcome();
loadConfig();

// ---------------- Start screen ----------------
document.getElementById("btn-play").addEventListener("click", startGame);

async function startGame() {
  const errEl = document.getElementById("start-error");
  errEl.textContent = "";
  try {
    const res = await fetch(`${API}/api/game/new`, { method: "POST" });
    if (!res.ok) throw new Error("Server error starting game");
    const data = await res.json();
    gameId = data.game_id;
    totalScore = 0;
    updateHud(0, 0);
    loadRound(data.round);
    showScreen("game");
  } catch (e) {
    errEl.textContent = "Couldn't reach the game server. Is the backend running?";
    console.error(e);
  }
}

// ---------------- Game screen ----------------
function updateHud(roundIndex, score) {
  document.getElementById("hud-player").textContent = playerName;
  document.getElementById("hud-round").textContent = roundIndex + 1;
  document.getElementById("hud-score").textContent = score;
}

function loadRound(round) {
  currentRoundIndex = round.round_index;
  pendingGuess = null;
  document.getElementById("btn-guess").disabled = true;
  document.getElementById("pin-hint").textContent = "Click the map to drop your pin";
  updateHud(currentRoundIndex, totalScore);

  renderScene(round);

  if (smallMap) {
    smallMap.remove();
    smallMap = null;
  }
  smallMap = L.map("map", { zoomControl: false }).setView([20, 0], 2);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap",
  }).addTo(smallMap);

  smallMap.on("click", (e) => {
    pendingGuess = { lat: e.latlng.lat, lng: e.latlng.lng };
    if (smallMarker) smallMap.removeLayer(smallMarker);
    smallMarker = L.marker(e.latlng).addTo(smallMap);
    document.getElementById("btn-guess").disabled = false;
    document.getElementById("pin-hint").textContent = "Pin placed - move it or confirm your guess";
  });
}

// Show either a real 360 Mapillary panorama (when the round has an
// image_id and the backend has a Mapillary token configured) or the
// static fallback photo (drag/scroll simulated pan+zoom).
function renderScene(round) {
  const viewerEl = document.getElementById("scene-viewer");
  const imageEl = document.getElementById("scene-image");

  destroyPanoViewer();

  if (round.image_id && mapillaryEnabled && mapillaryToken && window.mapillary) {
    imageEl.classList.add("hidden");
    viewerEl.classList.remove("hidden");
    try {
      panoViewer = new mapillary.Viewer({
        accessToken: mapillaryToken,
        container: viewerEl,
        imageId: round.image_id,
      });
      return;
    } catch (e) {
      console.warn("Mapillary viewer failed, falling back to static photo.", e);
      destroyPanoViewer();
    }
  }

  viewerEl.classList.add("hidden");
  imageEl.classList.remove("hidden");
  imageEl.style.backgroundImage = `url(${round.image_url})`;
  setupPanZoom(imageEl);
}

function destroyPanoViewer() {
  if (panoViewer) {
    try {
      panoViewer.remove();
    } catch (e) {
      /* ignore */
    }
    panoViewer = null;
  }
}

// Simple pan (drag) + zoom (wheel) on the scene photo, simulating
// looking around a fixed panorama.
function setupPanZoom(el) {
  let scale = 1, posX = 0, posY = 0;
  let dragging = false, startX = 0, startY = 0;

  function apply() {
    el.style.transform = `scale(${scale}) translate(${posX}px, ${posY}px)`;
  }

  el.style.transform = "scale(1) translate(0px, 0px)";
  el.onmousedown = (e) => {
    dragging = true;
    startX = e.clientX - posX;
    startY = e.clientY - posY;
    el.style.cursor = "grabbing";
  };
  window.onmousemove = (e) => {
    if (!dragging) return;
    posX = e.clientX - startX;
    posY = e.clientY - startY;
    apply();
  };
  window.onmouseup = () => {
    dragging = false;
    el.style.cursor = "grab";
  };
  el.onwheel = (e) => {
    e.preventDefault();
    scale = Math.min(3, Math.max(1, scale - e.deltaY * 0.001));
    apply();
  };
}

document.getElementById("btn-expand").addEventListener("click", () => {
  document.getElementById("map-widget").classList.toggle("expanded");
  setTimeout(() => smallMap && smallMap.invalidateSize(), 210);
});

document.getElementById("btn-guess").addEventListener("click", submitGuess);

async function submitGuess() {
  if (!pendingGuess) return;
  const res = await fetch(`${API}/api/game/${gameId}/guess`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      round_index: currentRoundIndex,
      lat: pendingGuess.lat,
      lng: pendingGuess.lng,
    }),
  });
  const data = await res.json();
  totalScore = data.total_score;
  showRoundResult(data.result, data.game_over, data.next_round);
}

// ---------------- Result screen ----------------
function showRoundResult(result, gameOver, nextRound) {
  document.getElementById("result-headline").textContent =
    result.distance_km < 25 ? "Excellent guess!" : "Round result";
  document.getElementById("result-location").textContent =
    `${result.actual_city}, ${result.actual_country}`;
  document.getElementById("result-distance").textContent =
    `${result.distance_km} km`;
  document.getElementById("result-score").textContent =
    `${result.score} pts`;

  showScreen("result");

  if (resultMap) {
    resultMap.remove();
    resultMap = null;
  }
  resultMap = L.map("map-result").setView(
    [result.actual_lat, result.actual_lng],
    3
  );
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap",
  }).addTo(resultMap);

  const guessLatLng = [result.guess_lat, result.guess_lng];
  const actualLatLng = [result.actual_lat, result.actual_lng];
  L.marker(guessLatLng).addTo(resultMap).bindPopup("Your guess");
  L.marker(actualLatLng).addTo(resultMap).bindPopup("Actual location");
  L.polyline([guessLatLng, actualLatLng], { color: "#3fb950" }).addTo(resultMap);
  resultMap.fitBounds([guessLatLng, actualLatLng], { padding: [40, 40] });

  const nextBtn = document.getElementById("btn-next");
  nextBtn.textContent = gameOver ? "See final results" : "Next round";
  nextBtn.onclick = () => {
    if (gameOver) {
      showFinalSummary();
    } else {
      loadRound(nextRound);
      showScreen("game");
    }
  };
}

// ---------------- Final screen ----------------
async function showFinalSummary() {
  const res = await fetch(`${API}/api/game/${gameId}/summary`);
  const data = await res.json();

  document.getElementById("final-player").textContent = `${playerName} — `;
  document.getElementById("final-total").textContent =
    `${data.total_score} / ${data.max_possible}`;

  const body = document.getElementById("summary-body");
  body.innerHTML = "";
  data.rounds.forEach((r, i) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${i + 1}</td>
      <td>${r.actual_city}, ${r.actual_country}</td>
      <td>${r.distance_km} km</td>
      <td>${r.score}</td>
    `;
    body.appendChild(tr);
  });

  showScreen("final");
}

document.getElementById("btn-play-again").addEventListener("click", startGame);
