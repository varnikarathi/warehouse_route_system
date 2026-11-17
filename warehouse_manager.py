import os
from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from werkzeug.utils import secure_filename
import storage

warehouse_bp = Blueprint('warehouse', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def load_warehouses():
    return storage.load_warehouses()


def save_warehouses(data):
    return storage.save_warehouses(data)


@warehouse_bp.route('/add-warehouse', methods=['GET', 'POST'])
def add_warehouse():
    if 'user' not in session or session.get('role') != 'admin':
        flash("Admin privileges required to add logistics nodes.", "error")
        return redirect('/dashboard')

    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            city = request.form.get('city', '').strip()
            lat = float(request.form.get('lat', 0))
            lon = float(request.form.get('lon', 0))

            if not name or not city:
                flash("Node name and city are required.", "error")
                return redirect('/add-warehouse')

            warehouses = load_warehouses()
            warehouses.append({
                'name': name,
                'city': city,
                'location': {'lat': lat, 'lon': lon},
                'category': 'Logistics Hub',
                'items': []
            })
            save_warehouses(warehouses)
            flash(f"Logistics node '{name}' registered successfully.", "success")
            return redirect('/dashboard')

        except (KeyError, ValueError) as e:
            flash("Invalid geographic coordinates provided.", "error")
            return redirect('/add-warehouse')

    return render_template('add_warehouse.html', user=session.get('user'), role=session.get('role'))


@warehouse_bp.route('/warehouse/<int:wid>', methods=['GET', 'POST'])
def manage_items(wid):
    if 'user' not in session:
        return redirect('/login')

    warehouses = load_warehouses()
    if wid < 0 or wid >= len(warehouses):
        flash("Location not found.", "error")
        return redirect('/dashboard')

    if request.method == 'POST':
        try:
            item_name = request.form.get('item', '').strip()
            qty = int(request.form.get('quantity', 1))
            image_url = request.form.get('image_url', '').strip()
            image_file = request.files.get('image_file')

            image_path = image_url
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                image_file.save(filepath)
                image_path = url_for('static', filename=f'uploads/{filename}')

            warehouses[wid].setdefault('items', [])
            warehouses[wid]['items'].append({
                'name': item_name,
                'quantity': qty,
                'image': image_path
            })
            save_warehouses(warehouses)
            flash("Item added to location roster.", "success")
            return redirect(f'/warehouse/{wid}')

        except (KeyError, ValueError):
            flash("Invalid item payload.", "error")

    selected = warehouses[wid]
    items = selected.get('items', [])
    return render_template(
        'manage_items.html',
        warehouse=selected,
        wid=wid,
        items=items,
        user=session.get('user'),
        role=session.get('role')
    )


@warehouse_bp.route('/warehouse/<int:wid>/delete/<int:item_id>')
def delete_item(wid, item_id):
    if 'user' not in session:
        return redirect('/login')

    warehouses = load_warehouses()
    if wid < 0 or wid >= len(warehouses):
        return "Not found", 404

    items = warehouses[wid].get('items', [])
    if 0 <= item_id < len(items):
        del items[item_id]
        save_warehouses(warehouses)
        flash("Item removed.", "info")

    return redirect(f'/warehouse/{wid}')


@warehouse_bp.route('/warehouse/<int:wid>/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(wid, item_id):
    if 'user' not in session:
        return redirect('/login')

    warehouses = load_warehouses()
    if wid < 0 or wid >= len(warehouses):
        return "Not found", 404

    items = warehouses[wid].get('items', [])
    if item_id < 0 or item_id >= len(items):
        return "Item not found", 404

    item = items[item_id]

    if request.method == 'POST':
        item['name'] = request.form.get('item', '').strip()
        item['quantity'] = int(request.form.get('quantity', 1))
        image_url = request.form.get('image_url', '').strip()
        image_file = request.files.get('image_file')

        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            image_file.save(filepath)
            item['image'] = url_for('static', filename=f'uploads/{filename}')
        elif image_url:
            item['image'] = image_url

        save_warehouses(warehouses)
        flash("Item updated.", "success")
        return redirect(f'/warehouse/{wid}')

    return render_template(
        'edit_item.html',
        item=item,
        wid=wid,
        item_id=item_id,
        user=session.get('user'),
        role=session.get('role')
    )
