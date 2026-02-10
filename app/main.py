from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from pathlib import Path
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -------------------------------------------------
# ENV
# -------------------------------------------------
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Real-Time Commute Predictor")

# -------------------------------------------------
# PREDEFINED JAMMU LOCATIONS (SOURCE OF TRUTH)
# -------------------------------------------------
JAMMU_LOCATIONS = {
    "Bahu Plaza": (74.8570, 32.7085),
    "Gandhi Nagar": (74.8741, 32.7064),
    "Channi": (74.8605, 32.6880),
    "Bathindi": (74.8297, 32.6826),
}

# -------------------------------------------------
# REQUEST SESSION
# -------------------------------------------------
def create_session():
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=1)
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s

session = create_session()

# -------------------------------------------------
# FRONTEND
# -------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# -------------------------------------------------
# OSRM ROUTING (STABLE)
# -------------------------------------------------
def osrm_route(src, dst):
    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{src[0]},{src[1]};{dst[0]},{dst[1]}"
        f"?overview=full&geometries=geojson"
    )

    res = session.get(url, timeout=20)
    data = res.json()

    if not data.get("routes"):
        return None

    route = data["routes"][0]
    return {
        "distance": route["distance"],
        "duration": route["duration"],
        "geometry": route["geometry"]["coordinates"]
    }

# -------------------------------------------------
# ETA API (JAMMU SAFE)
# -------------------------------------------------
@app.get("/eta")
def get_eta(source: str, destination: str):

    # ---- STRICT VALIDATION ----
    if source not in JAMMU_LOCATIONS:
        raise HTTPException(400, "Invalid source location")

    if destination not in JAMMU_LOCATIONS:
        raise HTTPException(400, "Invalid destination location")

    if source == destination:
        raise HTTPException(400, "Source and destination cannot be same")

    # ---- USE TRUSTED COORDS ----
    src = JAMMU_LOCATIONS[source]
    dst = JAMMU_LOCATIONS[destination]

    route = osrm_route(src, dst)
    if not route:
        raise HTTPException(404, "No route found")

    distance_km = round(route["distance"] / 1000, 2)
    duration_min = round(route["duration"] / 60, 2)

    geometry = [[lat, lon] for lon, lat in route["geometry"]]

    return {
        "distance": f"{distance_km} km",
        "duration_normal": f"{duration_min} mins",
        "geometry": geometry
    }

