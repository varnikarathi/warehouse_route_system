/* ==========================================================================
   ROUTEFLOW Interactive Route Planner Workspace
   Leaflet Mapping, Multi-Stop TSP Optimization, and Route Management
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Map
  const defaultCenter = [25.5941, 85.1376]; // Patna coordinates
  const map = L.map('planner-map', {
    zoomControl: false
  }).setView(defaultCenter, 8);

  L.control.zoom({ position: 'bottomright' }).addTo(map);

  // Sleek, minimal CartoDB Positron / OSM tiles
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    maxZoom: 19
  }).addTo(map);

  // State variables
  let intermediateStops = [];
  let currentRouteLayer = null;
  let activeMarkers = [];
  let lastCalculatedRoute = null;

  // Custom Minimalist SVG Markers
  function createMarkerIcon(label, type) {
    let bgColor = '#6366f1'; // Indigo for waypoint
    if (type === 'start') bgColor = '#10b981'; // Green for start
    if (type === 'dest') bgColor = '#ef4444'; // Red for destination

    const svgHtml = `
      <div style="
        background-color: ${bgColor};
        color: #ffffff;
        width: 26px;
        height: 26px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: Inter, sans-serif;
        font-weight: 700;
        font-size: 11px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.25);
        border: 2px solid #ffffff;
      ">${label}</div>
    `;

    return L.divIcon({
      html: svgHtml,
      className: 'rf-custom-marker',
      iconSize: [26, 26],
      iconAnchor: [13, 13]
    });
  }

  // Update Map Markers
  function refreshMapMarkers() {
    // Clear existing markers
    activeMarkers.forEach(m => map.removeLayer(m));
    activeMarkers = [];

    // 1. Start Marker
    const startCoordsStr = document.getElementById('startCoords').value;
    const startName = document.getElementById('startLocationName').value || 'Origin';
    if (startCoordsStr) {
      const [lon, lat] = startCoordsStr.split(',').map(Number);
      if (!isNaN(lat) && !isNaN(lon)) {
        const m = L.marker([lat, lon], {
          icon: createMarkerIcon('A', 'start'),
          draggable: true
        }).addTo(map);
        m.bindPopup(`<strong>Origin:</strong> ${startName}`);
        m.on('dragend', (e) => {
          const pos = e.target.getLatLng();
          document.getElementById('startCoords').value = `${pos.lng.toFixed(5)},${pos.lat.toFixed(5)}`;
        });
        activeMarkers.push(m);
      }
    }

    // 2. Intermediate Waypoint Markers
    intermediateStops.forEach((stop, idx) => {
      if (stop.coords) {
        const [lon, lat] = stop.coords;
        const m = L.marker([lat, lon], {
          icon: createMarkerIcon(String(idx + 1), 'waypoint'),
          draggable: true
        }).addTo(map);
        m.bindPopup(`<strong>Stop ${idx + 1}:</strong> ${stop.name}`);
        m.on('dragend', (e) => {
          const pos = e.target.getLatLng();
          stop.coords = [parseFloat(pos.lng.toFixed(5)), parseFloat(pos.lat.toFixed(5))];
          renderIntermediateStops();
        });
        activeMarkers.push(m);
      }
    });

    // 3. Destination Marker
    const destCoordsStr = document.getElementById('destCoords').value;
    const destName = document.getElementById('destLocationName').value || 'Destination';
    if (destCoordsStr) {
      const [lon, lat] = destCoordsStr.split(',').map(Number);
      if (!isNaN(lat) && !isNaN(lon)) {
        const m = L.marker([lat, lon], {
          icon: createMarkerIcon('B', 'dest'),
          draggable: true
        }).addTo(map);
        m.bindPopup(`<strong>Destination:</strong> ${destName}`);
        m.on('dragend', (e) => {
          const pos = e.target.getLatLng();
          document.getElementById('destCoords').value = `${pos.lng.toFixed(5)},${pos.lat.toFixed(5)}`;
        });
        activeMarkers.push(m);
      }
    }
  }

  // Render Intermediate Stops DOM
  function renderIntermediateStops() {
    const container = document.getElementById('intermediateStopsContainer');
    container.innerHTML = '';

    intermediateStops.forEach((stop, index) => {
      const card = document.createElement('div');
      card.className = 'stop-item-card';
      card.innerHTML = `
        <div class="stop-marker-badge stop-waypoint">${index + 1}</div>
        <div style="flex: 1;">
          <input type="text" class="stop-input-field stop-name-input" data-index="${index}" value="${stop.name}" placeholder="Stop address or name...">
        </div>
        <div class="stop-actions">
          ${index > 0 ? `<button type="button" class="stop-action-btn move-up-btn" data-index="${index}" title="Move up"><i data-lucide="chevron-up" style="width: 13px; height: 13px;"></i></button>` : ''}
          ${index < intermediateStops.length - 1 ? `<button type="button" class="stop-action-btn move-down-btn" data-index="${index}" title="Move down"><i data-lucide="chevron-down" style="width: 13px; height: 13px;"></i></button>` : ''}
          <button type="button" class="stop-action-btn remove-stop-btn" data-index="${index}" title="Remove stop" style="color: var(--danger);"><i data-lucide="trash-2" style="width: 13px; height: 13px;"></i></button>
        </div>
      `;
      container.appendChild(card);
    });

    if (window.lucide) window.lucide.createIcons();

    // Re-bind listeners for dynamic elements
    container.querySelectorAll('.stop-name-input').forEach(input => {
      input.addEventListener('change', (e) => {
        const idx = parseInt(e.target.dataset.index);
        intermediateStops[idx].name = e.target.value;
        refreshMapMarkers();
      });
    });

    container.querySelectorAll('.remove-stop-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const idx = parseInt(e.currentTarget.dataset.index);
        intermediateStops.splice(idx, 1);
        renderIntermediateStops();
        refreshMapMarkers();
      });
    });

    container.querySelectorAll('.move-up-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const idx = parseInt(e.currentTarget.dataset.index);
        if (idx > 0) {
          const temp = intermediateStops[idx];
          intermediateStops[idx] = intermediateStops[idx - 1];
          intermediateStops[idx - 1] = temp;
          renderIntermediateStops();
          refreshMapMarkers();
        }
      });
    });

    container.querySelectorAll('.move-down-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const idx = parseInt(e.currentTarget.dataset.index);
        if (idx < intermediateStops.length - 1) {
          const temp = intermediateStops[idx];
          intermediateStops[idx] = intermediateStops[idx + 1];
          intermediateStops[idx + 1] = temp;
          renderIntermediateStops();
          refreshMapMarkers();
        }
      });
    });

    refreshMapMarkers();
  }

  // Add Intermediate Stop
  function addStop(name, coords) {
    intermediateStops.push({
      name: name || `Stop ${intermediateStops.length + 1}`,
      coords: coords || [85.0425, 25.6262] // Danapur area fallback
    });
    renderIntermediateStops();
  }

  document.getElementById('addStopBtn').addEventListener('click', () => {
    addStop();
  });

  // Hub Preset Dropdown Selection
  const hubPresetSelect = document.getElementById('hubPresetSelect');
  if (hubPresetSelect) {
    hubPresetSelect.addEventListener('change', (e) => {
      const val = e.target.value;
      if (!val) return;
      const opt = e.target.selectedOptions[0];
      const name = opt.dataset.name || opt.innerText;
      const [lon, lat] = val.split(',').map(Number);

      addStop(name, [lon, lat]);
      hubPresetSelect.value = '';
    });
  }

  // Map Click to Add Stop
  map.on('click', (e) => {
    const lat = parseFloat(e.latlng.lat.toFixed(5));
    const lon = parseFloat(e.latlng.lng.toFixed(5));
    addStop(`Waypoint (${lat}, ${lon})`, [lon, lat]);
  });

  // Clear / Reset Route
  document.getElementById('clearRouteBtn').addEventListener('click', () => {
    intermediateStops = [];
    renderIntermediateStops();
    if (currentRouteLayer) {
      map.removeLayer(currentRouteLayer);
      currentRouteLayer = null;
    }
    document.getElementById('resultsPanel').style.display = 'none';
    refreshMapMarkers();
  });

  // Execute Route Optimization / Calculation
  async function performRouteCalculation(optimize = false) {
    const startName = document.getElementById('startLocationName').value || 'Origin';
    const startCoordsStr = document.getElementById('startCoords').value;
    const destName = document.getElementById('destLocationName').value || 'Destination';
    const destCoordsStr = document.getElementById('destCoords').value;

    if (!startCoordsStr || !destCoordsStr) {
      alert('Please configure valid start and destination locations.');
      return;
    }

    const [startLon, startLat] = startCoordsStr.split(',').map(Number);
    const [destLon, destLat] = destCoordsStr.split(',').map(Number);

    const waypoints = [
      { name: startName, coords: [startLon, startLat] },
      ...intermediateStops,
      { name: destName, coords: [destLon, destLat] }
    ];

    // Show loading
    document.getElementById('plannerLoading').style.display = 'block';
    document.getElementById('resultsPanel').style.display = 'none';

    try {
      const response = await fetch('/api/route/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          waypoints: waypoints,
          optimize: optimize,
          name: `${startName} to ${destName}`
        })
      });

      const data = await response.json();
      document.getElementById('plannerLoading').style.display = 'none';

      if (data.status !== 'success') {
        alert(data.message || 'Route calculation failed.');
        return;
      }

      lastCalculatedRoute = data;

      // Draw polyline on Map
      if (currentRouteLayer) {
        map.removeLayer(currentRouteLayer);
      }

      // Convert [lon, lat] to [lat, lon] for Leaflet
      const latLngs = data.geometry.map(pt => [pt[1], pt[0]]);
      currentRouteLayer = L.polyline(latLngs, {
        color: '#4f46e5',
        weight: 5,
        opacity: 0.9,
        lineJoin: 'round'
      }).addTo(map);

      map.fitBounds(currentRouteLayer.getBounds(), { padding: [40, 40] });

      // Update Waypoints order in UI if optimized
      if (data.optimized && data.waypoints && data.waypoints.length > 2) {
        intermediateStops = data.waypoints.slice(1, -1);
        renderIntermediateStops();
      }

      // Render Results Panel
      document.getElementById('resultDistance').innerText = `${data.distance_km} km`;
      document.getElementById('resultDuration').innerText = `${data.duration_min} mins`;

      const badge = document.getElementById('optimizationBadge');
      if (data.optimized) {
        badge.className = 'badge badge-success';
        badge.innerText = 'Optimized';
      } else {
        badge.className = 'badge badge-muted';
        badge.innerText = 'Standard';
      }

      const savingsBanner = document.getElementById('savingsBanner');
      if (data.optimized && data.distance_saved_km > 0) {
        savingsBanner.style.display = 'flex';
        document.getElementById('savedDistanceKm').innerText = `${data.distance_saved_km} km`;
        document.getElementById('savedTimeMin').innerText = `${data.time_saved_min} mins`;
      } else {
        savingsBanner.style.display = 'none';
      }

      // Sequence List
      const seqList = document.getElementById('sequenceList');
      seqList.innerHTML = '';
      data.waypoints.forEach(wp => {
        const li = document.createElement('li');
        li.innerText = wp.name;
        seqList.appendChild(li);
      });

      // Turn Guidance
      const dirList = document.getElementById('directionsList');
      dirList.innerHTML = '';
      document.getElementById('stepCount').innerText = (data.steps || []).length;
      (data.steps || []).forEach(step => {
        const item = document.createElement('div');
        item.style.padding = '0.35rem 0.5rem';
        item.style.backgroundColor = 'var(--bg-subtle)';
        item.style.borderRadius = '4px';
        item.innerHTML = `
          <div style="font-weight: 500; color: var(--text-main); font-size: 0.775rem;">${step.instruction}</div>
          <div style="font-size: 0.7rem; color: var(--text-muted);">${step.distance_km} km &bull; ${step.duration_min} min</div>
        `;
        dirList.appendChild(item);
      });

      document.getElementById('resultsPanel').style.display = 'block';

      if (window.lucide) window.lucide.createIcons();

    } catch (err) {
      document.getElementById('plannerLoading').style.display = 'none';
      console.error('Calculation error:', err);
      alert('Network or service exception during route calculation.');
    }
  }

  // Optimize Button
  document.getElementById('optimizeBtn').addEventListener('click', () => {
    performRouteCalculation(true);
  });

  // Calculate Sequential Button
  document.getElementById('calculateSeqBtn').addEventListener('click', () => {
    performRouteCalculation(false);
  });

  // Save Route Modal Handling
  const saveModal = document.getElementById('saveRouteModal');
  const openSaveModalBtn = document.getElementById('openSaveModalBtn');
  const closeSaveModalBtn = document.getElementById('closeSaveModalBtn');
  const cancelSaveBtn = document.getElementById('cancelSaveBtn');
  const confirmSaveRouteBtn = document.getElementById('confirmSaveRouteBtn');

  if (openSaveModalBtn) {
    openSaveModalBtn.addEventListener('click', () => {
      const startName = document.getElementById('startLocationName').value || 'Origin';
      const destName = document.getElementById('destLocationName').value || 'Destination';
      document.getElementById('saveRouteTitle').value = `${startName} to ${destName} Route`;
      saveModal.classList.add('show');
    });
  }

  function closeSaveModal() {
    saveModal.classList.remove('show');
  }

  if (closeSaveModalBtn) closeSaveModalBtn.addEventListener('click', closeSaveModal);
  if (cancelSaveBtn) cancelSaveBtn.addEventListener('click', closeSaveModal);

  if (confirmSaveRouteBtn) {
    confirmSaveRouteBtn.addEventListener('click', async () => {
      if (!lastCalculatedRoute) return;

      const title = document.getElementById('saveRouteTitle').value.trim();
      const tagsStr = document.getElementById('saveRouteTags').value.trim();
      const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()) : ['Planned'];

      const startCoords = document.getElementById('startCoords').value.split(',').map(Number);
      const destCoords = document.getElementById('destCoords').value.split(',').map(Number);

      const payload = {
        name: title,
        source: document.getElementById('startLocationName').value,
        destination: document.getElementById('destLocationName').value,
        source_coords: startCoords,
        dest_coords: destCoords,
        stops: intermediateStops,
        distance_km: lastCalculatedRoute.distance_km,
        duration_min: lastCalculatedRoute.duration_min,
        optimized: lastCalculatedRoute.optimized,
        distance_saved_km: lastCalculatedRoute.distance_saved_km,
        time_saved_min: lastCalculatedRoute.time_saved_min,
        tags: tags
      };

      try {
        const res = await fetch('/api/route/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const resData = await res.json();
        if (resData.status === 'success') {
          closeSaveModal();
          alert('Route successfully saved to your fleet library!');
        } else {
          alert('Failed to save route.');
        }
      } catch (e) {
        console.error(e);
        alert('Error saving route.');
      }
    });
  }

  // Preloaded Route Handling (e.g. from Saved Routes "Reopen in Planner")
  if (window.ROUTEFLOW_DATA && window.ROUTEFLOW_DATA.preloadedRoute) {
    const r = window.ROUTEFLOW_DATA.preloadedRoute;
    document.getElementById('startLocationName').value = r.source || 'Origin';
    if (r.source_coords) {
      document.getElementById('startCoords').value = `${r.source_coords[0]},${r.source_coords[1]}`;
    }
    document.getElementById('destLocationName').value = r.destination || 'Destination';
    if (r.dest_coords) {
      document.getElementById('destCoords').value = `${r.dest_coords[0]},${r.dest_coords[1]}`;
    }

    if (r.stops && Array.isArray(r.stops)) {
      intermediateStops = r.stops.map(s => ({
        name: s.name || 'Stop',
        coords: s.coords || [85.0425, 25.6262]
      }));
    }

    renderIntermediateStops();
    performRouteCalculation(r.optimized || false);
  } else {
    // Initial default render
    renderIntermediateStops();
    refreshMapMarkers();
  }
});
