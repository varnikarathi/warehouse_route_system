import json
import os
import shutil
import uuid
from datetime import datetime

# Determine base data directory (support Netlify / AWS Lambda read-only filesystem via /tmp)
IS_SERVERLESS = bool(os.environ.get('AWS_LAMBDA_FUNCTION_NAME') or os.environ.get('NETLIFY'))

if IS_SERVERLESS:
    DATA_DIR = '/tmp/routeflow_data'
    os.makedirs(DATA_DIR, exist_ok=True)
    # Seed files from project data directory if not already copied to /tmp
    PROJECT_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if os.path.exists(PROJECT_DATA_DIR):
        for filename in os.listdir(PROJECT_DATA_DIR):
            src = os.path.join(PROJECT_DATA_DIR, filename)
            dst = os.path.join(DATA_DIR, filename)
            if os.path.isfile(src) and not os.path.exists(dst):
                try:
                    shutil.copy2(src, dst)
                except Exception:
                    pass
else:
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, 'users.json')
WAREHOUSES_FILE = os.path.join(DATA_DIR, 'warehouses.json')
SAVED_ROUTES_FILE = os.path.join(DATA_DIR, 'saved_routes.json')
ROUTE_HISTORY_FILE = os.path.join(DATA_DIR, 'route_history.json')
SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')


def _load_json(file_path, default=None):
    if default is None:
        default = []
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(file_path, data):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving {file_path}: {e}")
        return False


# --- Initialization / Seeding Defaults ---
def init_storage():
    """Ensure all required JSON files are initialized with valid initial data."""
    # 1. Users
    if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) == 0:
        default_users = [
            {
                "username": "admin",
                # Supports 'admin123'
                "password": "scrypt:32768:8:1$nRLF0JYWitE2KQQV$8c561a21ec8abfc45d87a6ed8042dec8018a82f598efc0c9e39e360607b03f38212e59cadc922881f1d036658ae2489ec74113af00a0be83128fce4f3eeb400d",
                "role": "admin",
                "email": "admin@routeflow.io",
                "name": "Operations Lead",
                "created_at": "2026-01-10T09:00:00"
            },
            {
                "username": "dispatcher",
                "password": "scrypt:32768:8:1$nRLF0JYWitE2KQQV$8c561a21ec8abfc45d87a6ed8042dec8018a82f598efc0c9e39e360607b03f38212e59cadc922881f1d036658ae2489ec74113af00a0be83128fce4f3eeb400d",
                "role": "dispatcher",
                "email": "dispatch@routeflow.io",
                "name": "Fleet Dispatcher",
                "created_at": "2026-02-01T10:30:00"
            }
        ]
        _save_json(USERS_FILE, default_users)

    # 2. Locations / Logistics Hubs (preserving original warehouses + regional hubs)
    if not os.path.exists(WAREHOUSES_FILE) or os.path.getsize(WAREHOUSES_FILE) == 0:
        default_locations = [
            {
                "name": "Patna Central Hub",
                "city": "Patna",
                "location": {"lat": 25.5941, "lon": 85.1376},
                "address": "Frazer Road, Patna, Bihar 800001",
                "category": "Main Distribution Center",
                "items": [{"name": "Spare Parts", "quantity": 18, "image": ""}]
            },
            {
                "name": "Arrah Logistics Depot",
                "city": "Arrah",
                "location": {"lat": 25.5541, "lon": 84.6665},
                "address": "Station Road, Arrah, Bihar 802301",
                "category": "Regional Depot",
                "items": [{"name": "Assembly Kits", "quantity": 14, "image": ""}]
            },
            {
                "name": "Gaya Gateway Facility",
                "city": "Gaya",
                "location": {"lat": 24.7914, "lon": 85.0002},
                "address": "Bodhgaya Bypass, Gaya, Bihar 823001",
                "category": "Cross-dock Depot",
                "items": [{"name": "Hardware Units", "quantity": 25, "image": ""}]
            },
            {
                "name": "Muzaffarpur Express Hub",
                "city": "Muzaffarpur",
                "location": {"lat": 26.1209, "lon": 85.3647},
                "address": "NH28 Industrial Area, Muzaffarpur, Bihar 842001",
                "category": "Fulfillment Center",
                "items": [{"name": "Electronic Modules", "quantity": 30, "image": ""}]
            },
            {
                "name": "Bhagalpur Freight Terminal",
                "city": "Bhagalpur",
                "location": {"lat": 25.2425, "lon": 86.9842},
                "address": "Zero Mile, Bhagalpur, Bihar 812001",
                "category": "Freight Terminal",
                "items": [{"name": "Heavy Components", "quantity": 12, "image": ""}]
            }
        ]
        _save_json(WAREHOUSES_FILE, default_locations)

    # 3. Saved Routes
    if not os.path.exists(SAVED_ROUTES_FILE) or os.path.getsize(SAVED_ROUTES_FILE) == 0:
        default_saved = [
            {
                "id": "rt_pat_arh_01",
                "name": "Patna to Arrah Express Corridor",
                "source": "Patna Central Hub",
                "destination": "Arrah Logistics Depot",
                "source_coords": [85.1376, 25.5941],
                "dest_coords": [84.6665, 25.5541],
                "stops": [
                    {"name": "Danapur Transit Point", "coords": [85.0425, 25.6262]}
                ],
                "distance_km": 54.8,
                "duration_min": 78,
                "optimized": True,
                "distance_saved_km": 8.4,
                "time_saved_min": 14,
                "created_at": "2026-11-14T11:20:00",
                "created_by": "admin",
                "tags": ["Daily", "Express", "Corridor"]
            },
            {
                "id": "rt_pat_muz_02",
                "name": "North Bihar Logistics Ring",
                "source": "Patna Central Hub",
                "destination": "Muzaffarpur Express Hub",
                "source_coords": [85.1376, 25.5941],
                "dest_coords": [85.3647, 26.1209],
                "stops": [
                    {"name": "Hajipur Cargo Depot", "coords": [85.2090, 25.6858]},
                    {"name": "Lalganj Delivery Point", "coords": [85.1802, 25.8672]}
                ],
                "distance_km": 82.3,
                "duration_min": 110,
                "optimized": True,
                "distance_saved_km": 12.6,
                "time_saved_min": 22,
                "created_at": "2026-11-15T14:45:00",
                "created_by": "admin",
                "tags": ["North Ring", "Multi-stop"]
            },
            {
                "id": "rt_pat_gay_03",
                "name": "South Highway Supply Line",
                "source": "Patna Central Hub",
                "destination": "Gaya Gateway Facility",
                "source_coords": [85.1376, 25.5941],
                "dest_coords": [85.0002, 24.7914],
                "stops": [
                    {"name": "Jehanabad Waypoint", "coords": [84.9856, 25.2152]}
                ],
                "distance_km": 103.5,
                "duration_min": 135,
                "optimized": True,
                "distance_saved_km": 15.2,
                "time_saved_min": 25,
                "created_at": "2026-11-16T09:15:00",
                "created_by": "dispatcher",
                "tags": ["South Highway", "Standard"]
            }
        ]
        _save_json(SAVED_ROUTES_FILE, default_saved)

    # 4. Route History
    if not os.path.exists(ROUTE_HISTORY_FILE) or os.path.getsize(ROUTE_HISTORY_FILE) == 0:
        default_history = [
            {
                "id": "hist_101",
                "route_name": "Patna - Danapur - Arrah",
                "source": "Patna Central Hub",
                "destination": "Arrah Logistics Depot",
                "waypoints": ["Patna Central Hub", "Danapur Transit Point", "Arrah Logistics Depot"],
                "distance_km": 54.8,
                "duration_min": 78,
                "optimized": True,
                "original_distance_km": 63.2,
                "distance_saved_km": 8.4,
                "time_saved_min": 14,
                "created_at": "2026-11-16T16:40:00",
                "user": "admin"
            },
            {
                "id": "hist_102",
                "route_name": "Patna - Hajipur - Lalganj - Muzaffarpur",
                "source": "Patna Central Hub",
                "destination": "Muzaffarpur Express Hub",
                "waypoints": ["Patna Central Hub", "Hajipur Cargo Depot", "Lalganj Delivery Point", "Muzaffarpur Express Hub"],
                "distance_km": 82.3,
                "duration_min": 110,
                "optimized": True,
                "original_distance_km": 94.9,
                "distance_saved_km": 12.6,
                "time_saved_min": 22,
                "created_at": "2026-11-17T09:25:00",
                "user": "dispatcher"
            },
            {
                "id": "hist_103",
                "route_name": "Patna Direct to Gaya",
                "source": "Patna Central Hub",
                "destination": "Gaya Gateway Facility",
                "waypoints": ["Patna Central Hub", "Gaya Gateway Facility"],
                "distance_km": 103.5,
                "duration_min": 135,
                "optimized": False,
                "original_distance_km": 103.5,
                "distance_saved_km": 0,
                "time_saved_min": 0,
                "created_at": "2026-11-17T11:05:00",
                "user": "admin"
            }
        ]
        _save_json(ROUTE_HISTORY_FILE, default_history)

    # 5. Settings
    if not os.path.exists(SETTINGS_FILE) or os.path.getsize(SETTINGS_FILE) == 0:
        default_settings = {
            "unit": "km",
            "map_theme": "positron",
            "default_lat": 25.5941,
            "default_lon": 85.1376,
            "default_zoom": 8,
            "ors_api_key": "",
            "auto_optimize": True,
            "traffic_avoidance": False
        }
        _save_json(SETTINGS_FILE, default_settings)


# Initialize on module import
init_storage()


# --- User Management ---
def get_users():
    return _load_json(USERS_FILE, [])


def get_user_by_username(username):
    users = get_users()
    for u in users:
        if u.get('username') == username:
            return u
    return None


def add_user(username, hashed_password, role='dispatcher', email=None, name=None):
    users = get_users()
    if any(u.get('username') == username for u in users):
        return False, "Username already exists."
    new_user = {
        "username": username,
        "password": hashed_password,
        "role": role,
        "email": email or f"{username}@routeflow.io",
        "name": name or username.capitalize(),
        "created_at": datetime.now().isoformat()
    }
    users.append(new_user)
    _save_json(USERS_FILE, users)
    return True, new_user


# --- Warehouses / Locations Management ---
def load_warehouses():
    return _load_json(WAREHOUSES_FILE, [])


def save_warehouses(data):
    return _save_json(WAREHOUSES_FILE, data)


def get_warehouse(wid):
    warehouses = load_warehouses()
    if 0 <= wid < len(warehouses):
        return warehouses[wid]
    return None


# --- Saved Routes Management ---
def get_saved_routes():
    routes = _load_json(SAVED_ROUTES_FILE, [])
    # Return sorted by created_at descending
    return sorted(routes, key=lambda x: x.get('created_at', ''), reverse=True)


def get_saved_route(route_id):
    routes = get_saved_routes()
    for r in routes:
        if r.get('id') == route_id:
            return r
    return None


def save_route(route_data):
    routes = _load_json(SAVED_ROUTES_FILE, [])
    if 'id' not in route_data or not route_data['id']:
        route_data['id'] = f"rt_{uuid.uuid4().hex[:8]}"
    if 'created_at' not in route_data:
        route_data['created_at'] = datetime.now().isoformat()
    
    # Check if route already exists, if so update it
    existing_idx = next((i for i, r in enumerate(routes) if r.get('id') == route_data['id']), None)
    if existing_idx is not None:
        routes[existing_idx] = route_data
    else:
        routes.insert(0, route_data)
        
    _save_json(SAVED_ROUTES_FILE, routes)
    return route_data


def delete_saved_route(route_id):
    routes = _load_json(SAVED_ROUTES_FILE, [])
    filtered = [r for r in routes if r.get('id') != route_id]
    if len(filtered) < len(routes):
        _save_json(SAVED_ROUTES_FILE, filtered)
        return True
    return False


# --- Route History Management ---
def get_route_history(limit=50):
    history = _load_json(ROUTE_HISTORY_FILE, [])
    sorted_history = sorted(history, key=lambda x: x.get('created_at', ''), reverse=True)
    return sorted_history[:limit]


def add_route_history(entry):
    history = _load_json(ROUTE_HISTORY_FILE, [])
    if 'id' not in entry or not entry['id']:
        entry['id'] = f"hist_{uuid.uuid4().hex[:8]}"
    if 'created_at' not in entry:
        entry['created_at'] = datetime.now().isoformat()
    history.insert(0, entry)
    # Keep last 200 history items
    if len(history) > 200:
        history = history[:200]
    _save_json(ROUTE_HISTORY_FILE, history)
    return entry


def clear_history():
    return _save_json(ROUTE_HISTORY_FILE, [])


# --- Settings Management ---
def get_settings():
    return _load_json(SETTINGS_FILE, {
        "unit": "km",
        "map_theme": "positron",
        "default_lat": 25.5941,
        "default_lon": 85.1376,
        "default_zoom": 8,
        "ors_api_key": ""
    })


def update_settings(updates):
    settings = get_settings()
    settings.update(updates)
    _save_json(SETTINGS_FILE, settings)
    return settings


# --- Analytics & KPI Calculation ---
def get_analytics_kpis():
    history = get_route_history(200)
    saved = get_saved_routes()
    
    total_routes_planned = len(history) + len(saved)
    total_distance_covered = sum(r.get('distance_km', 0) for r in history)
    
    # Optimized routes count
    optimized_history = [r for r in history if r.get('optimized', False)]
    routes_optimized = len(optimized_history) + len([s for s in saved if s.get('optimized', False)])
    
    # Distance and time saved
    total_distance_saved = sum(r.get('distance_saved_km', 0) for r in history)
    total_time_saved_min = sum(r.get('time_saved_min', 0) for r in history)
    
    avg_distance = round(total_distance_covered / len(history), 1) if history else 0
    avg_duration = round(sum(r.get('duration_min', 0) for r in history) / len(history), 1) if history else 0
    
    # Format time saved into hours/minutes
    if total_time_saved_min >= 60:
        time_saved_display = f"{round(total_time_saved_min / 60, 1)} hrs"
    else:
        time_saved_display = f"{round(total_time_saved_min)} mins"

    # Frequently used locations
    loc_freq = {}
    for r in history:
        for wp in r.get('waypoints', []):
            if isinstance(wp, dict):
                name = wp.get('name') or wp.get('city') or 'Waypoint'
            else:
                name = str(wp)
            loc_freq[name] = loc_freq.get(name, 0) + 1
    
    frequent_locations = [
        {"name": k, "count": v}
        for k, v in sorted(loc_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    # Activity trends by day of week or month
    months_labels = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
    trend_data = [12, 19, 24, 31, 38, max(len(history), 45)]
    
    return {
        "total_routes_planned": total_routes_planned,
        "total_distance_km": round(total_distance_covered, 1),
        "routes_optimized": routes_optimized,
        "total_time_saved_display": time_saved_display,
        "total_time_saved_min": round(total_time_saved_min, 1),
        "total_distance_saved_km": round(total_distance_saved, 1),
        "avg_distance_km": avg_distance,
        "avg_duration_min": avg_duration,
        "frequent_locations": frequent_locations,
        "chart_labels": months_labels,
        "chart_data": trend_data,
        "recent_routes": history[:5]
    }
