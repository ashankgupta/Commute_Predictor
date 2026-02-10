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
# ENV + PATH SETUP
# -------------------------------------------------
load_dotenv()

ORS_API_KEY = os.getenv("ORS_API_KEY")
if not ORS_API_KEY:
    raise RuntimeError("ORS_API_KEY not found in .env")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app = FastAPI(title="Real-Time Commute Predictor")

# -------------------------------------------------
# REQUESTS SESSION WITH RETRY
# -------------------------------------------------
def create_session():
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    return session

session = create_session()

# -------------------------------------------------
# FRONTEND
# -------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# -------------------------------------------------
# GEOCODING (ORS → NOMINATIM FALLBACK)
# -------------------------------------------------
def geocode(place: str):
    # --- Try ORS Geocoding ---
    try:
        url = "https://api.openrouteservice.org/geocode/search"
        params = {
            "api_key": ORS_API_KEY,
            "text": place,
            "size": 1
        }
        res = session.get(url, params=params, timeout=20)
        data = res.json()

        if data.get("features"):
            return data["features"][0]["geometry"]["coordinates"]  # [lon, lat]

    except Exception as e:
        print("ORS geocoding failed, fallback to Nominatim:", e)

    # --- Fallback: Nominatim ---
    nom_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": place,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "CommutePredictor/1.0"
    }

    res = session.get(nom_url, params=params, headers=headers, timeout=10)
    data = res.json()

    if not data:
        raise HTTPException(404, f"Location not found: {place}")

    lon = float(data[0]["lon"])
    lat = float(data[0]["lat"])
    return [lon, lat]

# -------------------------------------------------
# OSRM FALLBACK ROUTING (VERY RELIABLE)
# -------------------------------------------------
def osrm_route(src, dst):
    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{src[0]},{src[1]};{dst[0]},{dst[1]}"
        f"?overview=full&geometries=geojson"
    )

    res = session.get(url, timeout=20)
    data = res.json()

    if data.get("routes"):
        route = data["routes"][0]
        return {
            "distance": route["distance"],
            "duration": route["duration"],
            "geometry": route["geometry"]["coordinates"]
        }

    return None

# -------------------------------------------------
# ETA + ROUTE API
# -------------------------------------------------
@app.get("/eta")
def get_eta(source: str, destination: str):

    # 1. Geocode
    src_coords = geocode(source)
    dst_coords = geocode(destination)

    print("SRC:", src_coords, "DST:", dst_coords)

    # 2. Try ORS routing
    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "coordinates": [src_coords, dst_coords],
        "geometry": True,
        "geometry_format": "geojson"
    }

    profiles = ["driving-car", "driving-hgv", "cycling-regular"]
    data = None

    for profile in profiles:
        try:
            url = f"https://api.openrouteservice.org/v2/directions/{profile}"
            res = session.post(url, json=body, headers=headers, timeout=25)
            temp = res.json()

            if temp.get("routes"):
                data = temp
                break

        except Exception as e:
            print(f"ORS routing failed ({profile}):", e)

    # -------------------------------------------------
    # ORS SUCCESS
    # -------------------------------------------------
    if data:
        route = data["routes"][0]
        summary = route["summary"]

        distance_km = round(summary["distance"] / 1000, 2)
        duration_min = round(summary["duration"] / 60, 2)

        geometry = [
            [coord[1], coord[0]]
            for coord in route["geometry"]["coordinates"]
        ]

        return {
            "distance": f"{distance_km} km",
            "duration_normal": f"{duration_min} mins",
            "duration_in_traffic": f"{duration_min} mins",
            "geometry": geometry
        }

    # -------------------------------------------------
    # ORS FAILED → OSRM FALLBACK
    # -------------------------------------------------
    osrm = osrm_route(src_coords, dst_coords)

    if not osrm:
        raise HTTPException(404, "No route found (ORS + OSRM failed)")

    distance_km = round(osrm["distance"] / 1000, 2)
    duration_min = round(osrm["duration"] / 60, 2)

    geometry = [
        [coord[1], coord[0]]
        for coord in osrm["geometry"]
    ]

    return {
        "distance": f"{distance_km} km",
        "duration_normal": f"{duration_min} mins",
        "duration_in_traffic": f"{duration_min} mins",
        "geometry": geometry
    }

