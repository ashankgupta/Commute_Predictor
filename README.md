# Commute Predictor - Jammu

## Overview
This project is a real-time commute predictor and traffic simulator focused on the city of Jammu. It provides a web-based interface to visualize fixed routes, simulate car movements, and calculate estimated travel times (ETA) between locations using various geocoding and routing services.

## Features
*   **Interactive Map**: Visualize traffic routes and car movements on a Leaflet map.
*   **Fixed Routes Simulation**: Simulate predefined routes within Jammu with animated car icons.
*   **Location Focus**: Ability to focus the map on specific key locations in Jammu.
*   **ETA Calculation API**: A backend API to calculate estimated travel times and distances between a source and destination.
*   **Geocoding**: Utilizes OpenRouteService (ORS) and Nominatim for converting place names to geographic coordinates.
*   **Routing**: Employs OpenRouteService (ORS) and Open Source Routing Machine (OSRM) for calculating optimal routes and travel durations.

## Technologies Used
*   **Backend**:
    *   FastAPI: A modern, fast (high-performance) web framework for building APIs with Python.
    *   Python-dotenv: For managing environment variables.
    *   Requests: HTTP library for making API calls.
    *   Jinja2: Templating engine for rendering HTML.
*   **Frontend**:
    *   HTML, CSS (Tailwind CSS for styling)
    *   JavaScript
    *   Leaflet.js: An open-source JavaScript library for interactive maps.
*   **Mapping & Routing Services**:
    *   OpenRouteService (ORS)
    *   Nominatim (OpenStreetMap geocoding)
    *   Open Source Routing Machine (OSRM)

## Setup and Installation

### Prerequisites
*   Python 3.8+
*   An API key from OpenRouteService (ORS). You can obtain one by registering at [https://openrouteservice.org/](https://openrouteservice.org/).

### Steps

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/ashankgupta/Commute_Predictor.git
    cd Commute_Predictor
    ```

2.  **Create a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    Create a `.env` file in the root directory of the project and add your OpenRouteService API key:
    ```
    ORS_API_KEY="YOUR_OPENROUTESERVICE_API_KEY"
    ```
    Replace `"YOUR_OPENROUTESERVICE_API_KEY"` with the actual API key you obtained.

5.  **Run the application**:
    ```bash
    uvicorn app.main:app --reload
    ```
    The application will typically run on `http://127.0.0.1:8000`.

## Usage

### Web Interface
Open your web browser and navigate to `http://127.0.0.1:8000/`. You will see the interactive map of Jammu with simulated traffic. You can:
*   Select a "Focus Location" from the dropdown to center the map on a specific area.
*   Observe the simulated cars moving along predefined routes.

### API Endpoint

The application exposes an API endpoint for calculating ETA and route geometry:

**GET /eta**
Calculates the estimated travel time and provides route geometry between two locations.

*   **Parameters**:
    *   `source` (string, required): The starting location (e.g., "Bahu Plaza").
    *   `destination` (string, required): The ending location (e.g., "Gandhi Nagar").

*   **Example Request**:
    ```
    GET http://127.0.0.1:8000/eta?source=Bahu%20Plaza&destination=Gandhi%20Nagar
    ```

*   **Example Response**:
    ```json
    {
      "distance": "X.XX km",
      "duration_normal": "YY.YY mins",
      "duration_in_traffic": "YY.YY mins",
      "geometry": [
        [lat1, lon1],
        [lat2, lon2],
        ...
      ]
    }
    ```
    Note: `duration_in_traffic` currently returns the same value as `duration_normal` as real-time traffic data integration is not yet fully implemented.
