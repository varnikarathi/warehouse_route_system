# ROUTEFLOW &mdash; Intelligent Route Optimization & Logistics Planning Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.1-black.svg)](https://palletsprojects.com/p/flask/)
[![UI Style](https://img.shields.io/badge/Design-Linear%20%2F%20Stripe%20%2F%20Vercel-indigo.svg)](#design-system--philosophy)
[![Maps](https://img.shields.io/badge/Mapping-Leaflet%20%2B%20CartoDB%20Positron-emerald.svg)](https://leafletjs.com/)

**ROUTEFLOW** is a modern, minimal, premium Route Optimization and Logistics Planning SaaS platform. Designed for fleet dispatchers, logistics coordinators, and freight operators, ROUTEFLOW combines intelligent multi-stop route sequencing with an interactive mapping workspace, real-time KPI metrics, and complete audit logging.

Inspired by the refined aesthetics of **Linear**, **Stripe Dashboard**, and **Vercel**, ROUTEFLOW replaces cluttered legacy admin dashboards with generous whitespace, crisp typography, subtle borders, and seamless interactive controls.

---

## Table of Contents

1. [Design System & Philosophy](#design-system--philosophy)
2. [Key Features](#key-features)
3. [Architecture Overview](#architecture-overview)
4. [Tech Stack](#tech-stack)
5. [Getting Started (Local Development)](#getting-started-local-development)
6. [Application Walkthrough](#application-walkthrough)
7. [REST API Reference](#rest-api-reference)
8. [Configuration & Environment Variables](#configuration--environment-variables)

---

## Design System & Philosophy

ROUTEFLOW adheres strictly to modern SaaS design standards:

- **Minimalist Palette**: Clean white (`#ffffff`) and off-white (`#f8fafc`) canvas, crisp slate borders (`#e2e8f0`), charcoal typography (`#0f172a`), and a subtle indigo accent (`#4f46e5`).
- **Typography Hierarchy**: Powered by **Inter** with optimized letter-spacing (`-0.02em` for headlines) and monospace numeric accents.
- **Micro-interactions**: Subtle hover states, smooth transitions (`150ms cubic-bezier`), and lightweight SVG Lucide icons.
- **Zero Clutter**: No heavy glassmorphism, aggressive gradient overlays, or bloated Bootstrap cards. Every UI element serves an operational purpose.

---

## Key Features

### 1. Interactive Split-Screen Route Planner (Core Feature)
- **Left Panel — Route Configuration**:
  - Specify Origin and Destination with interactive coordinate geocoding.
  - Dynamically **Add, Remove, and Reorder** intermediate delivery stops.
  - Quick-load logistics hubs and regional depots from dropdown presets.
  - **One-Click TSP Route Optimization**: Algorithms calculate the shortest path through intermediate waypoints.
  - **Sequential Mode**: Compare standard order against the optimized sequence.
  - **Live Savings Summary**: Immediate visibility into distance saved (km) and driving time reduced (mins).
  - Turn-by-turn guidance drawer with segment distances.
- **Right Panel — Interactive Mapping Workspace**:
  - Full-viewport Leaflet map styled with CartoDB Positron minimalist basemaps.
  - Custom minimal SVG markers:
    - **A**: Green origin pin
    - **1, 2, ... N**: Indigo intermediate waypoint pins
    - **B**: Red destination pin
  - Draggable markers to fine-tune locations directly on the map.
  - **Click-to-Add Waypoint**: Click anywhere on the map to add stops on the fly.
  - Route line rendering with smooth polyline styling and dynamic bounds auto-fitting.

### 2. High-Performance Executive Dashboard
- **Live KPI Metrics**:
  - Total Routes Planned
  - Total Distance Covered (km)
  - Routes Optimized
  - Estimated Time Saved (hours / minutes)
- **Activity Trends**: Chart.js monthly volume curves with minimalist gridlines and custom tooltips.
- **Optimization Ratio**: Visual doughnut breakdown of optimized vs. standard journeys.
- **Recent Routes Table**: Quick overview of recent corridors with one-click reload in the Planner.
- **Frequently Used Locations**: Track highest-frequency logistics hubs and trip counts.

### 3. Saved Routes Fleet Library
- Save pre-configured routes with custom titles and tags (e.g. *Daily North Corridor Express*).
- Filter and search routes by title, origin, or destination.
- **One-Click Reopen**: Instantly reload any saved route into the interactive planner map.
- Delete and manage saved route records.

### 4. Route Audit History & CSV Export
- Comprehensive immutable log of every route calculation.
- Displays waypoints count, mileage, travel duration, optimization status, and dispatcher username.
- Search and filter by corridor, dispatcher, or status.
- **One-Click CSV Export**: Download the entire dispatch history as a formatted CSV spreadsheet.

### 5. Deep-Dive Analytics
- Optimization adoption rate analysis (`%` of routes optimized).
- Comparative bar charts tracking driven distance versus distance saved.
- Average route length and trip duration diagnostics.

### 6. Robust OpenRouteService Engine with Resilient Fallback
- Direct integration with OpenRouteService (`/v2/directions/driving-car/geojson`).
- **Security-First**: API keys remain strictly server-side &mdash; never leaked to frontend client code.
- **Graceful Offline/Sandbox Fallback**: If OpenRouteService rate limits or loses network connection, ROUTEFLOW automatically falls back to an intelligent road-factor geodesic routing engine with realistic curvature interpolation. The app remains 100% operational in any environment.

### 7. Authentication & Role-Based Access Control
- Secure password hashing with cryptographic `scrypt`.
- Session-based authentication with flash notifications.
- Role management (`admin`, `dispatcher`, `viewer`).
- User profile overview with operational contribution metrics.

---

## Architecture Overview

```
warehouse_route_system/
├── app.py                  # Core Flask application & REST API routes
├── auth.py                 # Authentication blueprint (Login, Register, Logout)
├── ors_service.py          # OpenRouteService API integration & TSP algorithm
├── storage.py              # Centralized JSON storage & serverless /tmp adapter
├── warehouse_manager.py    # Logistics hub & facility inventory management
├── requirements.txt        # Production Python dependencies
│
├── data/                   # Persistent JSON Storage Layer
│   ├── users.json          # User credentials & roles
│   ├── warehouses.json     # Logistics hubs, depots & facility coordinates
│   ├── saved_routes.json   # Saved fleet route library
│   ├── route_history.json  # Route planning audit logs
│   └── settings.json       # Platform & map preferences
│
├── static/
│   ├── css/
│   │   └── main.css        # Premium SaaS Design System (Linear / Stripe style)
│   └── js/
│       ├── main.js         # Sidebar toggle, Ctrl+K search, dropdowns
│       └── planner.js      # Split-screen Leaflet interactive route workspace
│
└── templates/              # Semantic Jinja2 Templates
    ├── base.html           # Master layout with slim sidebar & top navigation
    ├── dashboard.html      # Overview dashboard with KPI cards & Chart.js
    ├── planner.html        # Interactive split-screen route planner
    ├── saved_routes.html   # Fleet route library & filters
    ├── history.html        # Route calculation logs & CSV export
    ├── analytics.html      # Fleet intelligence & distance savings charts
    ├── profile.html        # User profile & dispatch statistics
    ├── settings.html       # Unit toggle, map theme & ORS API token config
    ├── add_warehouse.html  # Hub registration form
    ├── manage_items.html   # Facility item roster
    ├── edit_item.html      # Item editor
    └── auth/
        ├── login.html      # Minimalist sign-in card
        └── register.html   # Operator registration card
```

---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.11+, Flask 3.1, Werkzeug, Requests |
| **Routing Engine** | OpenRouteService API + Exact Permutation & Nearest-Neighbor TSP |
| **Frontend Styling** | Custom Modular CSS Design System (Inter typography, CSS Variables) |
| **Interactive Maps** | Leaflet.js 1.9, CartoDB Positron basemap tiles |
| **Data Visualizations** | Chart.js 4.4 |
| **Iconography** | Lucide Outline Icons |
| **Storage** | Atomic JSON persistence |

---

## Getting Started (Local Development)

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14 installed
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/warehouse_route_system.git
cd warehouse_route_system
```

### 2. Create and Activate Virtual Environment
**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```
The application will start on:
```
http://127.0.0.1:5000/
```

### 5. Default Credentials
| Username | Password | Role | Permissions |
| :--- | :--- | :--- | :--- |
| **admin** | `admin123` | Administrator | Full access to planner, hubs, analytics, and settings |
| **dispatcher** | `admin123` | Dispatcher | Planner, saved routes, history, and analytics |

*You can also register any new custom account at `/register`.*

---

## Application Walkthrough

### 1. Route Planning & Optimization
1. Navigate to **Route Planner** in the sidebar (or press `⌘K` / `Ctrl+K` and type `Planner`).
2. Origin defaults to *Patna Central Hub*, Destination to *Arrah Logistics Depot*.
3. Click **"Add Intermediate Stop"** or choose a pre-configured facility from the **"Quick Load Logistics Hub"** dropdown.
4. Alternatively, click directly on the interactive map to place a waypoint anywhere in the world!
5. Click **"Optimize Route"**:
   - The backend runs Travelling Salesperson waypoint sequencing.
   - The map animates and renders the optimal route polyline.
   - The results card details total mileage, driving time, and distance saved.
6. Click **"Save Route to Fleet Library"** to store the corridor with tags for recurring operations.

### 2. Managing Saved Routes
1. Navigate to **Saved Routes**.
2. Type in the search box for real-time corridor filtering.
3. Click **"Reopen"** on any route card &mdash; the entire configuration and intermediate stops are seamlessly reloaded onto the interactive map in the Route Planner!

### 3. Exporting Route Logs
1. Navigate to **Route History**.
2. Filter by status (`Optimized` or `Standard`).
3. Click **"Export CSV"** to instantly generate and download an audit spreadsheet.

---

## REST API Reference

All API endpoints require an authenticated session.

### 1. Calculate Route
- **URL**: `POST /api/route/calculate`
- **Request Body**:
```json
{
  "waypoints": [
    { "name": "Origin", "coords": [85.1376, 25.5941] },
    { "name": "Stop 1", "coords": [85.0425, 25.6262] },
    { "name": "Destination", "coords": [84.6665, 25.5541] }
  ],
  "optimize": true,
  "name": "North Corridor Express"
}
```
- **Response**:
```json
{
  "status": "success",
  "provider": "openrouteservice",
  "distance_km": 54.8,
  "duration_min": 78.0,
  "optimized": true,
  "distance_saved_km": 8.4,
  "time_saved_min": 14.0,
  "savings_pct": 13.3,
  "geometry": [[85.1376, 25.5941], [85.0425, 25.6262], ...],
  "steps": [
    { "instruction": "Depart from Origin toward Stop 1", "distance_km": 12.3, "duration_min": 18.0 }
  ],
  "waypoints": [...]
}
```

### 2. Save Route
- **URL**: `POST /api/route/save`
- **Request Body**:
```json
{
  "name": "South Expressway Ring",
  "source": "Patna Central Hub",
  "destination": "Gaya Gateway Facility",
  "source_coords": [85.1376, 25.5941],
  "dest_coords": [85.0002, 24.7914],
  "stops": [],
  "distance_km": 103.5,
  "duration_min": 135.0,
  "optimized": true,
  "tags": ["South Highway", "Express"]
}
```

### 3. Delete Saved Route
- **URL**: `DELETE /api/route/saved/<route_id>`
- **Response**: `{ "status": "success" }`

### 4. Fetch Logistics Hubs
- **URL**: `GET /api/locations`
- **Response**: List of registered facilities and geographic coordinates.

---

## Configuration & Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `SECRET_KEY` | Flask session encryption key | `routeflow_enterprise_secret_key_2026` |
| `ORS_API_KEY` | OpenRouteService API Key | Built-in fallback token |
| `PORT` | HTTP port for server binding | `5000` |

---

## License

This project is licensed under the MIT License.
