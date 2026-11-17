import os
import io
import csv
from flask import Flask, render_template, session, redirect, request, jsonify, flash, Response
from auth import auth_bp
from warehouse_manager import warehouse_bp
import storage
import ors_service

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'routeflow_enterprise_secret_key_2026')

# Register existing / legacy blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(warehouse_bp)


# --- Helper decorator / check ---
def login_required():
    return 'user' in session


# Global context processor for user and settings
@app.context_processor
def inject_global_data():
    settings = storage.get_settings()
    return {
        'current_user': session.get('user'),
        'current_role': session.get('role', 'dispatcher'),
        'current_name': session.get('name', session.get('user', 'Guest')),
        'app_settings': settings,
        'brand_name': 'ROUTEFLOW'
    }


# --- Main Dashboard ---
@app.route('/dashboard')
def dashboard():
    if not login_required():
        return redirect('/login')

    kpis = storage.get_analytics_kpis()
    warehouses = storage.load_warehouses()
    settings = storage.get_settings()

    return render_template(
        'dashboard.html',
        kpis=kpis,
        warehouses=warehouses,
        settings=settings,
        route=session.get('route')
    )


# --- Route Planner Workspace (Core Feature) ---
@app.route('/planner')
def planner():
    if not login_required():
        return redirect('/login')

    warehouses = storage.load_warehouses()
    settings = storage.get_settings()

    # Optional: pre-load a saved route if route_id is provided in query
    route_id = request.args.get('route_id')
    preloaded_route = None
    if route_id:
        preloaded_route = storage.get_saved_route(route_id)

    return render_template(
        'planner.html',
        warehouses=warehouses,
        settings=settings,
        preloaded_route=preloaded_route
    )


# --- Saved Routes ---
@app.route('/saved-routes')
def saved_routes():
    if not login_required():
        return redirect('/login')

    routes = storage.get_saved_routes()
    return render_template('saved_routes.html', routes=routes)


@app.route('/saved-routes/delete/<route_id>', methods=['POST', 'GET'])
def delete_saved_route_action(route_id):
    if not login_required():
        return redirect('/login')

    success = storage.delete_saved_route(route_id)
    if success:
        flash("Saved route removed successfully.", "success")
    else:
        flash("Route not found.", "error")
    return redirect('/saved-routes')


# --- Route History ---
@app.route('/history')
def history():
    if not login_required():
        return redirect('/login')

    history_list = storage.get_route_history(limit=100)
    return render_template('history.html', history=history_list)


@app.route('/history/export')
def export_history_csv():
    if not login_required():
        return redirect('/login')

    history_list = storage.get_route_history(limit=500)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Route ID", "Route Name", "Source", "Destination", "Waypoints Count",
        "Distance (km)", "Duration (min)", "Optimized", "Distance Saved (km)",
        "Time Saved (min)", "Created At", "Planned By"
    ])

    for h in history_list:
        writer.writerow([
            h.get('id', ''),
            h.get('route_name', ''),
            h.get('source', ''),
            h.get('destination', ''),
            len(h.get('waypoints', [])),
            h.get('distance_km', 0),
            h.get('duration_min', 0),
            "Yes" if h.get('optimized') else "No",
            h.get('distance_saved_km', 0),
            h.get('time_saved_min', 0),
            h.get('created_at', ''),
            h.get('user', '')
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=routeflow_history.csv"}
    )


# --- Analytics ---
@app.route('/analytics')
def analytics():
    if not login_required():
        return redirect('/login')

    kpis = storage.get_analytics_kpis()
    history_list = storage.get_route_history(limit=200)

    # Detailed statistics
    total_routes = len(history_list)
    optimized_count = sum(1 for h in history_list if h.get('optimized'))
    opt_rate = round((optimized_count / total_routes * 100), 1) if total_routes > 0 else 0
    total_dist = sum(h.get('distance_km', 0) for h in history_list)
    total_savings = sum(h.get('distance_saved_km', 0) for h in history_list)
    avg_dist = round(total_dist / total_routes, 1) if total_routes > 0 else 0

    return render_template(
        'analytics.html',
        kpis=kpis,
        total_routes=total_routes,
        optimized_count=optimized_count,
        optimization_rate=opt_rate,
        total_dist=round(total_dist, 1),
        total_savings=round(total_savings, 1),
        avg_dist=avg_dist
    )


# --- Profile ---
@app.route('/profile')
def profile():
    if not login_required():
        return redirect('/login')

    user = storage.get_user_by_username(session['user'])
    history_list = storage.get_route_history(limit=200)
    user_routes = [h for h in history_list if h.get('user') == session['user']]

    return render_template(
        'profile.html',
        profile_user=user or {},
        user_routes_count=len(user_routes),
        user_total_km=round(sum(h.get('distance_km', 0) for h in user_routes), 1)
    )


# --- Settings ---
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not login_required():
        return redirect('/login')

    if request.method == 'POST':
        unit = request.form.get('unit', 'km')
        map_theme = request.form.get('map_theme', 'positron')
        ors_api_key = request.form.get('ors_api_key', '').strip()
        auto_optimize = 'auto_optimize' in request.form

        storage.update_settings({
            'unit': unit,
            'map_theme': map_theme,
            'ors_api_key': ors_api_key,
            'auto_optimize': auto_optimize
        })
        flash("Application settings updated.", "success")
        return redirect('/settings')

    current_settings = storage.get_settings()
    return render_template('settings.html', settings=current_settings)


# --- REST API Endpoints ---
@app.route('/api/route/calculate', methods=['POST'])
def api_calculate_route():
    if not login_required():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.get_json() or {}
    waypoints = data.get('waypoints', [])
    optimize = bool(data.get('optimize', False))
    route_name = data.get('name')

    if len(waypoints) < 2:
        return jsonify({'status': 'error', 'message': 'At least 2 waypoints are required.'}), 400

    result = ors_service.calculate_route(waypoints, optimize=optimize)

    if result.get('status') == 'success':
        # Automatically record calculation to route history
        source_name = waypoints[0].get('name', 'Starting Point')
        dest_name = waypoints[-1].get('name', 'Destination')
        auto_name = route_name or f"{source_name} to {dest_name}"

        storage.add_route_history({
            'route_name': auto_name,
            'source': source_name,
            'destination': dest_name,
            'waypoints': [wp.get('name', 'Point') for wp in result.get('waypoints', waypoints)],
            'distance_km': result['distance_km'],
            'duration_min': result['duration_min'],
            'optimized': result.get('optimized', False),
            'original_distance_km': result.get('original_distance_km', result['distance_km']),
            'distance_saved_km': result.get('distance_saved_km', 0.0),
            'time_saved_min': result.get('time_saved_min', 0.0),
            'user': session.get('user', 'anonymous')
        })

    return jsonify(result)


@app.route('/api/route/save', methods=['POST'])
def api_save_route():
    if not login_required():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        name = f"Route {session.get('user')}_{storage.datetime.now().strftime('%b %d %H:%M')}"

    route_payload = {
        'id': data.get('id') or f"rt_{storage.uuid.uuid4().hex[:8]}",
        'name': name,
        'source': data.get('source', 'Starting Point'),
        'destination': data.get('destination', 'Destination'),
        'source_coords': data.get('source_coords'),
        'dest_coords': data.get('dest_coords'),
        'stops': data.get('stops', []),
        'distance_km': data.get('distance_km', 0),
        'duration_min': data.get('duration_min', 0),
        'optimized': bool(data.get('optimized', False)),
        'distance_saved_km': data.get('distance_saved_km', 0),
        'time_saved_min': data.get('time_saved_min', 0),
        'created_at': storage.datetime.now().isoformat(),
        'created_by': session.get('user'),
        'tags': data.get('tags', ['Planned'])
    }

    saved = storage.save_route(route_payload)
    return jsonify({'status': 'success', 'route': saved})


@app.route('/api/route/saved/<route_id>', methods=['DELETE'])
def api_delete_saved_route(route_id):
    if not login_required():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    success = storage.delete_saved_route(route_id)
    if success:
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Route not found'}), 404


@app.route('/api/locations', methods=['GET'])
def api_locations():
    if not login_required():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    warehouses = storage.load_warehouses()
    return jsonify({'status': 'success', 'locations': warehouses})


# --- Backward Compatibility Route: /optimize-route ---
@app.route('/optimize-route', methods=['POST'])
def legacy_optimize_route():
    if not login_required():
        return redirect('/login')

    warehouses = storage.load_warehouses()
    try:
        source_idx = int(request.form['source'])
        dest_idx = int(request.form['destination'])
        source = warehouses[source_idx]
        destination = warehouses[dest_idx]

        waypoints = [
            {'name': source['name'], 'coords': [source['location']['lon'], source['location']['lat']]},
            {'name': destination['name'], 'coords': [destination['location']['lon'], destination['location']['lat']]}
        ]

        result = ors_service.calculate_route(waypoints, optimize=False)
        session['route'] = {
            'source': source['city'],
            'destination': destination['city'],
            'distance_km': result['distance_km'],
            'duration_min': result['duration_min'],
            'source_lat': source['location']['lat'],
            'source_lon': source['location']['lon'],
            'destination_lat': destination['location']['lat'],
            'destination_lon': destination['location']['lon']
        }
        flash("Route calculated successfully.", "success")
    except Exception as e:
        flash(f"Error calculating route: {e}", "error")

    return redirect('/dashboard')


if __name__ == '__main__':
    storage.init_storage()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
