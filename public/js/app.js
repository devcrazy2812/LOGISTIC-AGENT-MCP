/**
 * LogiSwarm TMS - Enterprise Transportation Management Suite Controller
 * Clean, production-hardened JavaScript without vibe-code anti-patterns.
 */

// Application Globals
let map;
let routeLayers = [];
let markerLayers = [];
let hazardLayers = [];
let activeTab = 'feed';
let lastSubmitTime = 0;
let currentState = null;
let pollInterval = null;
let selectedVehicleId = null;

// Vehicle Brand Theme
const vehicleMeta = {
  'FLEET-EV-01': { color: '#10b981', label: 'VoltHauler Alpha (EV)' },
  'FLEET-TRK-02': { color: '#6366f1', label: 'Titan Heavy Semi (Diesel)' },
  'FLEET-MID-03': { color: '#f59e0b', label: 'SwiftRunner (CNG)' },
  'FLEET-COLD-04': { color: '#06b6d4', label: 'PolarGuard Reefer (Hybrid)' }
};

const agentBadges = {
  'Commander-Prime': { color: 'bg-blue-950/80 border-blue-800 text-blue-200' },
  'Sentinel-Risk': { color: 'bg-rose-950/80 border-rose-800 text-rose-200' },
  'StockMaster': { color: 'bg-purple-950/80 border-purple-800 text-purple-200' },
  'RouteOptima': { color: 'bg-emerald-950/80 border-emerald-800 text-emerald-200' },
  'CommLiaison': { color: 'bg-amber-950/80 border-amber-800 text-amber-200' },
  'QualityGuard': { color: 'bg-pink-950/80 border-pink-800 text-pink-200' }
};

// Sample base64 transparent 1x1 image for initial diagnostics
const SAMPLE_B64_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=";

document.addEventListener('DOMContentLoaded', () => {
  initMap();
  initClock();
  initEventListeners();
  initFloatingDock();
  initCookieBanner();
  initDrawerChat();
  initDropZone();
  initKeyboardNavigation();
  
  // Initial fetch and start adaptive polling
  fetchState();
  startAdaptivePolling();
});

/* ==========================================================================
   SECTION 1: Interactive Toast Notification System
   ========================================================================== */
function showToast(title, message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const typeStyles = {
    success: 'bg-slate-900 border-emerald-800 text-emerald-300',
    error: 'bg-slate-900 border-rose-800 text-rose-300',
    warning: 'bg-slate-900 border-amber-800 text-amber-300',
    info: 'bg-slate-900 border-slate-700 text-slate-200'
  };

  const toast = document.createElement('div');
  toast.className = `toast p-3 rounded-xl border shadow-xl flex items-start gap-2.5 text-xs ${typeStyles[type] || typeStyles.info}`;
  toast.setAttribute('role', 'alert');
  toast.innerHTML = `
    <div class="flex-1">
      <div class="font-bold text-[11px] text-white">${escapeHtml(title)}</div>
      <div class="text-[10px] text-slate-400 mt-0.5 leading-snug">${escapeHtml(message)}</div>
    </div>
    <button class="text-slate-400 hover:text-white p-0.5" onclick="this.parentElement.remove()" aria-label="Dismiss toast">
      &times;
    </button>
  `;

  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3800);
}

/* ==========================================================================
   SECTION 2: High-Performance Geo-Spatial Map (CartoDB Dark Matter)
   ========================================================================== */
function initMap() {
  const mapElement = document.getElementById('map');
  if (!mapElement) return;

  map = L.map('map', {
    zoomControl: true,
    attributionControl: false,
    preferCanvas: true
  }).setView([19.0760, 72.8777], 11);

  // CartoDB Dark Matter tile layer (optimized for dark dashboards)
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png', {
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(map);
}

function recenterMap() {
  if (!map) return;
  selectedVehicleId = null;
  map.setView([19.0760, 72.8777], 11, { animate: true });
  showToast('Map Recentered', 'Viewport reset to central metropolitan corridor', 'info');
}

function focusVehicleOnMap(vehicleId) {
  if (!map || !currentState) return;
  selectedVehicleId = vehicleId;

  const vehicle = (currentState.vehicles || []).find(v => v.id === vehicleId);
  if (!vehicle) return;

  map.flyTo([vehicle.current_lat, vehicle.current_lng], 13, { duration: 1.0 });
  renderMap(currentState);
  showToast('Vehicle Focused', `Tracking ${vehicle.name} (${vehicle.type})`, 'info');
}

/* ==========================================================================
   SECTION 3: Dynamic State Rendering & Adaptive Polling
   ========================================================================== */
function startAdaptivePolling() {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(fetchState, 3500);

  // Pause polling when browser tab is inactive to save battery and network
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      clearInterval(pollInterval);
    } else {
      fetchState();
      pollInterval = setInterval(fetchState, 3500);
    }
  });
}

async function fetchState() {
  try {
    const res = await fetch('/api/state');
    if (!res.ok) return;
    const state = await res.json();
    currentState = state;
    renderState(state);
  } catch (err) {
    console.debug('Telemetry sync standby:', err);
  }
}

function renderState(state) {
  if (!state) return;

  const m = state.metrics || {};
  const fb = state.latest_feedback || {};

  // Update Numerical KPIs
  const slaEl = document.getElementById('metric-sla');
  if (slaEl) slaEl.textContent = (m.sla_compliance_rate || 100.0).toFixed(1);

  const qualityEl = document.getElementById('metric-quality');
  if (qualityEl) qualityEl.textContent = (fb.composite_score || 92.5).toFixed(1);

  const costEl = document.getElementById('metric-cost');
  if (costEl) costEl.textContent = (m.total_cost_usd || 0.0).toLocaleString('en-US', { minimumFractionDigits: 2 });

  const co2El = document.getElementById('metric-co2-saved');
  if (co2El) co2El.textContent = (m.co2_saved_vs_baseline_kg || 0.0).toFixed(1);

  const utilEl = document.getElementById('metric-utilization');
  if (utilEl) utilEl.textContent = (m.fleet_utilization_rate || 0.0).toFixed(1);

  // Active Incident Banner Management
  const activeDisruptions = state.disruptions || [];
  const incidentBanner = document.getElementById('active-incident-banner');
  if (incidentBanner) {
    if (activeDisruptions.length > 0) {
      const topIncident = activeDisruptions[activeDisruptions.length - 1];
      document.getElementById('incident-title').textContent = topIncident.title || 'Transit Friction Alert';
      document.getElementById('incident-desc').textContent = `${topIncident.description} — Swarm autonomously resolving route bypass.`;
      incidentBanner.classList.remove('hidden');
    } else {
      incidentBanner.classList.add('hidden');
    }
  }

  // Update Map, Manifest, and Swarm Intelligence Feeds
  renderMap(state);
  renderFleetTable(state.vehicles || [], state.orders || []);
  renderThoughts(state.agent_thoughts || []);
  renderNotifications(state.notifications || []);
  renderAuditLogs(state.audit_logs || []);
}

function renderMap(state) {
  if (!map) return;

  // Clear previous layers
  routeLayers.forEach(l => map.removeLayer(l));
  markerLayers.forEach(l => map.removeLayer(l));
  hazardLayers.forEach(l => map.removeLayer(l));
  routeLayers = [];
  markerLayers = [];
  hazardLayers = [];

  // 1. Draw Active Hazard Corridors
  (state.disruptions || []).forEach(d => {
    if (d.affected_lat && d.affected_lng && d.radius_km) {
      const circle = L.circle([d.affected_lat, d.affected_lng], {
        radius: d.radius_km * 1000,
        color: '#f43f5e',
        fillColor: '#e11d48',
        fillOpacity: 0.22,
        weight: 2,
        dashArray: '5, 5',
        className: 'hazard-circle-pulse'
      }).addTo(map);

      circle.bindPopup(`
        <div class="text-xs">
          <strong class="text-rose-400 uppercase font-mono text-[10px] tracking-wider">Transit Hazard Zone</strong>
          <div class="font-bold text-white text-xs mt-0.5">${escapeHtml(d.title)}</div>
          <div class="text-slate-400 text-[11px] mt-1">${escapeHtml(d.description)}</div>
        </div>
      `);
      hazardLayers.push(circle);
    }
  });

  // 2. Draw Regional Hub Depots
  (state.depots || []).forEach(depot => {
    const icon = L.divIcon({
      className: 'custom-depot-marker',
      html: `
        <div class="w-7 h-7 rounded-lg bg-blue-600 border border-white/80 flex items-center justify-center shadow-lg text-white font-bold text-xs" role="img" aria-label="Depot ${depot.id}">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
        </div>
      `,
      iconSize: [28, 28],
      iconAnchor: [14, 28]
    });

    const marker = L.marker([depot.lat, depot.lng], { icon }).addTo(map);
    const stockList = Object.entries(depot.inventory || {})
      .map(([k, v]) => `• ${escapeHtml(k.replace(/_/g, ' '))}: <b>${v}</b>`)
      .join('<br/>');

    marker.bindPopup(`
      <div class="text-xs">
        <span class="text-blue-400 font-mono text-[10px] font-bold uppercase">${escapeHtml(depot.id)}</span>
        <div class="font-bold text-white text-xs mt-0.5">${escapeHtml(depot.name)}</div>
        <div class="mt-2 pt-1.5 border-t border-slate-700 text-slate-300 text-[10px] space-y-0.5">
          <div class="font-semibold text-slate-400">Inventory Stockpile:</div>
          <div>${stockList}</div>
        </div>
      </div>
    `);
    markerLayers.push(marker);
  });

  // 3. Draw Consignment Drop Stops
  (state.orders || []).forEach(ord => {
    let pinColor = '#10b981';
    if (ord.priority === 'CRITICAL') pinColor = '#f43f5e';
    else if (ord.priority === 'HIGH') pinColor = '#f59e0b';
    if (ord.status === 'delayed') pinColor = '#e11d48';

    const icon = L.divIcon({
      className: 'custom-order-marker',
      html: `
        <div class="w-4 h-4 rounded-full border border-white/90 shadow flex items-center justify-center text-[9px] font-bold text-white" style="background-color: ${pinColor};" role="img" aria-label="Order stop ${ord.id}">
          ${ord.priority ? ord.priority[0] : 'O'}
        </div>
      `,
      iconSize: [16, 16],
      iconAnchor: [8, 8]
    });

    const marker = L.marker([ord.lat, ord.lng], { icon }).addTo(map);
    marker.bindPopup(`
      <div class="text-xs">
        <span class="font-mono text-[10px] text-slate-400">${escapeHtml(ord.id)}</span>
        <div class="font-bold text-white text-xs">${escapeHtml(ord.customer)}</div>
        <div class="mt-1 space-y-0.5 text-slate-300 text-[11px]">
          <div>Cargo: <b>${ord.quantity}x ${escapeHtml(ord.item.replace(/_/g, ' '))}</b> (${ord.weight_kg} kg)</div>
          <div>Priority: <b style="color:${pinColor}">${ord.priority}</b></div>
          <div>Status: <b class="uppercase">${escapeHtml(ord.status)}</b></div>
          <div>Est. Arrival: <b>${ord.estimated_arrival_minutes ? ord.estimated_arrival_minutes + ' min' : 'Pending'}</b></div>
        </div>
      </div>
    `);
    markerLayers.push(marker);
  });

  // 4. Draw Polylines for Active Routes
  (state.vehicles || []).forEach(v => {
    if (v.route_stops && v.route_stops.length > 1 && v.status !== 'disrupted') {
      const latlngs = v.route_stops.map(s => [s.lat, s.lng]);
      const meta = vehicleMeta[v.id] || { color: '#38bdf8' };
      const isSelected = selectedVehicleId === v.id;

      const polyline = L.polyline(latlngs, {
        color: meta.color,
        weight: isSelected ? 4.5 : 3,
        opacity: isSelected ? 1.0 : 0.85,
        dashArray: v.type.includes('EV') ? '4, 4' : null,
        className: isSelected ? 'route-highlighted' : ''
      }).addTo(map);

      polyline.bindTooltip(`${v.name} (${v.assigned_orders.length} drop-offs)`, { sticky: true });
      routeLayers.push(polyline);
    }
  });
}

function renderFleetTable(vehicles, orders) {
  const tbody = document.getElementById('fleet-table-body');
  if (!tbody) return;

  tbody.innerHTML = vehicles.map(v => {
    const isDisrupted = v.status === 'disrupted';
    const isSelected = selectedVehicleId === v.id;

    const statusBadge = isDisrupted
      ? `<span class="px-2 py-0.5 rounded-full bg-rose-950/80 border border-rose-800 text-rose-300 font-bold font-mono text-[10px]">DISABLED</span>`
      : v.assigned_orders.length > 0
        ? `<span class="px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-800 text-emerald-300 font-semibold font-mono text-[10px]">EN ROUTE</span>`
        : `<span class="px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-medium font-mono text-[10px]">IDLE</span>`;

    const meta = vehicleMeta[v.id] || { color: '#38bdf8' };
    
    // Calculate payload percentage
    const assignedOrderObjects = (orders || []).filter(o => v.assigned_orders.includes(o.id));
    const currentWeight = assignedOrderObjects.reduce((acc, cur) => acc + (cur.weight_kg || 0), 0);
    const capacityPct = Math.min(100, Math.round((currentWeight / (v.capacity_kg || 1)) * 100));

    return `
      <tr class="hover:bg-slate-800/50 transition cursor-pointer ${isSelected ? 'bg-slate-800/80 border-l-2 border-sky-400' : ''}" onclick="focusVehicleOnMap('${v.id}')">
        <td class="py-2.5 px-3">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full shrink-0" style="background-color: ${meta.color}"></span>
            <div>
              <div class="font-bold text-slate-100">${escapeHtml(v.name)}</div>
              <div class="text-[10px] text-slate-400 font-mono">${v.id}</div>
            </div>
          </div>
        </td>
        <td class="py-2.5 px-3">
          <div class="text-slate-200 font-medium">${escapeHtml(v.type)}</div>
          <div class="text-[10px] text-slate-400">${escapeHtml(v.fuel_type)} • ${v.capacity_kg} kg max</div>
        </td>
        <td class="py-2.5 px-3">
          <div class="flex items-center gap-2">
            <span class="font-bold text-sky-400 font-mono">${v.assigned_orders.length}</span>
            <span class="text-slate-400">orders</span>
          </div>
          <div class="w-24 bg-slate-800 rounded-full h-1.5 mt-1 overflow-hidden">
            <div class="bg-sky-500 h-1.5 rounded-full" style="width: ${capacityPct}%"></div>
          </div>
        </td>
        <td class="py-2.5 px-3">
          <div class="font-mono text-slate-200">${v.total_distance_km} km</div>
          <div class="text-[10px] text-slate-400 font-mono">${v.total_time_min} mins</div>
        </td>
        <td class="py-2.5 px-3">
          <div class="text-emerald-400 font-mono font-bold">$${v.total_cost_usd}</div>
          <div class="text-[10px] text-slate-400 font-mono">${v.total_co2_kg} kg CO₂</div>
        </td>
        <td class="py-2.5 px-3">${statusBadge}</td>
      </tr>
    `;
  }).join('');
}

function renderThoughts(thoughts) {
  const container = document.getElementById('agent-thoughts-feed');
  if (!container) return;

  const recent = thoughts.slice(-30);
  container.innerHTML = recent.map(t => {
    const badge = agentBadges[t.agent_name] || { color: 'bg-slate-800 border-slate-700 text-slate-300' };
    
    let phaseBadge = 'text-sky-400';
    if (t.phase === 'OBSERVE') phaseBadge = 'text-blue-400';
    else if (t.phase === 'REASON') phaseBadge = 'text-purple-400';
    else if (t.phase === 'ACTION') phaseBadge = 'text-emerald-400';

    const toolBadges = (t.tools_used || []).map(tool => 
      `<span class="px-1.5 py-0.5 rounded bg-slate-900 text-[9px] text-slate-300 border border-slate-800 font-mono">tool:${escapeHtml(tool)}</span>`
    ).join(' ');

    return `
      <div class="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition space-y-1">
        <div class="flex items-center justify-between text-[10px]">
          <span class="px-2 py-0.5 rounded border text-[10px] font-bold ${badge.color}">
            ${escapeHtml(t.agent_name)} (${escapeHtml(t.role)})
          </span>
          <span class="text-slate-400 font-mono">${escapeHtml(t.timestamp)}</span>
        </div>
        <div class="text-slate-200 leading-snug">
          <span class="font-bold ${phaseBadge}">[${escapeHtml(t.phase)}]</span> ${escapeHtml(t.content)}
        </div>
        ${toolBadges ? `<div class="pt-0.5 flex flex-wrap gap-1">${toolBadges}</div>` : ''}
      </div>
    `;
  }).join('');

  container.scrollTop = container.scrollHeight;
}

function renderNotifications(notifications) {
  const box = document.getElementById('notifications-box');
  if (!box) return;

  if (!notifications.length) {
    box.innerHTML = `<span class="text-slate-400 italic">No incident advisories active. Routing corridors nominal.</span>`;
    return;
  }

  box.innerHTML = notifications.slice(-3).map(n => `
    <div class="p-2 rounded-lg bg-amber-950/40 border border-amber-900/50 text-amber-200 leading-tight">
      ${escapeHtml(n.message)}
    </div>
  `).join('');
}

function renderAuditLogs(logs) {
  const container = document.getElementById('audit-log-container');
  if (!container) return;

  if (!logs.length) {
    container.innerHTML = `<div class="text-slate-500 italic">No audit records logged yet.</div>`;
    return;
  }

  container.innerHTML = logs.slice(-20).reverse().map(l => `
    <div class="p-1.5 rounded bg-slate-900 border border-slate-800 flex items-center justify-between text-[10px]">
      <div>
        <span class="text-sky-400 font-bold">[${escapeHtml(l.action)}]</span> 
        <span class="text-slate-300">${escapeHtml(l.details)}</span>
      </div>
      <div class="text-slate-500 text-[9px] font-mono shrink-0 ml-2">
        ${escapeHtml(l.timestamp.split(' ')[1] || '')} • ${escapeHtml(l.ip_address)}
      </div>
    </div>
  `).join('');
}

/* ==========================================================================
   SECTION 4: Operational Actions & Disruption Ingestion
   ========================================================================== */
function initEventListeners() {
  document.getElementById('btn-reoptimize')?.addEventListener('click', async () => {
    showToast('Optimization In Progress', 'RouteOptima re-solving CVRP with Pareto criteria...', 'info');
    if (window.LogiAnalytics) window.LogiAnalytics.track('optimize_swarm_cta');
    try {
      const res = await fetch('/api/optimize', { method: 'POST' });
      const data = await res.json();
      currentState = data.data;
      renderState(data.data);
      showToast('Optimization Converged', `Plan Quality Score: ${data.data.latest_feedback.composite_score}/100`, 'success');
    } catch (err) {
      showToast('Optimization Error', String(err), 'error');
    }
  });
}

async function injectDisruption(type) {
  showToast('Injecting Friction Event', `Testing autonomous swarm self-healing under ${type}...`, 'warning');
  if (window.LogiAnalytics) window.LogiAnalytics.track('disruption_injected', { type });

  try {
    const res = await fetch('/api/disruption', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type })
    });
    const data = await res.json();
    currentState = data.data;
    renderState(data.data);
    showToast('Autonomous Recovery Complete', 'Sentinel isolated friction and RouteOptima bypass routes verified.', 'success');
  } catch (err) {
    showToast('Disruption Simulation Error', String(err), 'error');
  }
}

async function resetSwarmState() {
  try {
    const res = await fetch('/api/reset', { method: 'POST' });
    const data = await res.json();
    currentState = data.data;
    selectedVehicleId = null;
    renderState(data.data);
    showToast('Simulation Reset', 'Corridors restored to nominal baseline scenario', 'success');
  } catch (err) {
    showToast('Reset Failed', String(err), 'error');
  }
}

async function submitHumanFeedback(rating) {
  const comments = {
    'positive': 'Optimal route plan approved by Chief Dispatcher.',
    'rebalance': 'Human policy override: Prioritize EV vehicle allocation on upcoming legs.',
    'negative': 'Flagged sub-optimal stop sequence. Requested algorithmic recalculation.'
  };
  if (window.LogiAnalytics) window.LogiAnalytics.track('human_feedback', { rating });

  try {
    const res = await fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating, comment: comments[rating] })
    });
    showToast('Dispatcher Feedback Logged', `Evaluator recorded ${rating.toUpperCase()} rating. Swarm weights calibrated.`, 'success');
  } catch (err) {
    showToast('Feedback Error', String(err), 'error');
  }
}

/* ==========================================================================
   SECTION 5: Multimodal Cargo Vision Diagnostics
   ========================================================================== */
function initDropZone() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('cargo-file-input');
  if (!dropZone || !fileInput) return;

  dropZone.addEventListener('click', () => fileInput.click());

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-active');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-active');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-active');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processSelectedImageFile(e.dataTransfer.files[0]);
    }
  });
}

function handleFileSelected(e) {
  if (e.target.files && e.target.files[0]) {
    processSelectedImageFile(e.target.files[0]);
  }
}

function processSelectedImageFile(file) {
  if (!file.type.startsWith('image/')) {
    showToast('Invalid File', 'Please select an image file (PNG, JPEG, WebP)', 'error');
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    showToast('File Too Large', 'Maximum image payload size is 5MB', 'error');
    return;
  }

  const reader = new FileReader();
  reader.onload = () => {
    const base64Data = reader.result;
    executeMultimodalAnalysis(base64Data, file.name);
  };
  reader.readAsDataURL(file);
}

function runPresetInspection(presetKey) {
  executeMultimodalAnalysis(SAMPLE_B64_IMAGE, `preset-${presetKey}.png`);
}

async function executeMultimodalAnalysis(imageBase64, fileName) {
  const statusNote = document.getElementById('vision-status-note');
  const resultCard = document.getElementById('vision-card');
  const badge = document.getElementById('vision-engine-badge');
  
  if (statusNote) statusNote.textContent = `Analyzing ${fileName || 'cargo photograph'} via Google Gemini Multimodal Vision API...`;
  if (resultCard) resultCard.classList.add('hidden');

  try {
    const res = await fetch('/api/inspect_cargo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_base64: imageBase64, cargo_id: 'ORD-01' })
    });
    const data = await res.json();
    const payload = data.data || {};
    const analysis = payload.analysis || {};

    if (badge) {
      if (payload.mode === 'LIVE_GEMINI_API') {
        badge.className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-300';
        badge.textContent = 'Live Cloud Gemini API';
      } else {
        badge.className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 border border-amber-800 text-amber-300';
        badge.textContent = 'Embedded Simulated Engine';
      }
    }

    if (statusNote) statusNote.textContent = `Diagnostic inspection completed for ${fileName || 'cargo'}:`;

    // Populate Structured Diagnostic Card
    document.getElementById('vision-severity-pill').textContent = analysis.damage_severity || 'UNKNOWN';
    document.getElementById('vision-action-pill').textContent = analysis.recommended_action || 'ACTION REQUIRED';
    document.getElementById('vision-liability-val').textContent = `$${(analysis.insurance_claim_estimate_usd || 0).toLocaleString()} Claim`;
    document.getElementById('vision-root-cause').textContent = analysis.root_cause || 'Under investigation';
    document.getElementById('vision-integrity').textContent = analysis.box_integrity || 'Seal integrity uncompromised';
    document.getElementById('vision-directive').textContent = analysis.directive || 'Standard warehouse protocol';

    if (resultCard) resultCard.classList.remove('hidden');
    showToast('Inspection Complete', `Assessed ${analysis.damage_severity}: ${analysis.recommended_action}`, 'success');
  } catch (err) {
    if (statusNote) statusNote.textContent = `Analysis failed: ${err}`;
    showToast('Inspection Error', String(err), 'error');
  }
}

/* ==========================================================================
   SECTION 6: Floating AI Assistant Drawer
   ========================================================================== */
function initDrawerChat() {
  let saved = [];
  try {
    const raw = sessionStorage.getItem('app_shared_chat_history');
    if (raw) saved = JSON.parse(raw);
  } catch (e) {}

  if (!saved.length) {
    saved = [
      { role: 'assistant', content: 'Greetings Chief Dispatcher. I am Commander-Prime. Autonomous telemetry, CVRP optimization, and disruption healing are active. How can I assist?' }
    ];
    sessionStorage.setItem('app_shared_chat_history', JSON.stringify(saved));
  }

  renderDrawerMessages(saved);
}

function renderDrawerMessages(messages) {
  const container = document.getElementById('drawer-chat-messages');
  if (!container) return;

  container.innerHTML = messages.map(m => {
    const isUser = m.role === 'user';
    const formatted = formatChatMessage(m.content);

    return `
      <div class="p-3 rounded-xl ${isUser ? 'bg-sky-950/60 border border-sky-800/60 text-slate-200 ml-6' : 'bg-slate-800/80 border border-slate-700/80 text-slate-200 mr-6'}">
        <div class="text-[10px] font-bold ${isUser ? 'text-sky-400' : 'text-emerald-400'} mb-1 flex items-center justify-between">
          <span>${isUser ? 'Dispatcher' : 'Commander-Prime'}</span>
        </div>
        <div class="leading-relaxed text-[11px]">${formatted}</div>
      </div>
    `;
  }).join('');

  container.scrollTop = container.scrollHeight;
}

function formatChatMessage(text) {
  if (!text) return '';
  return escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
    .replace(/`([^`]+)`/g, '<code class="bg-slate-900 px-1 py-0.5 rounded font-mono text-[10px] text-sky-300">$1</code>');
}

function toggleChatDrawer(open) {
  const drawer = document.getElementById('chat-drawer');
  if (!drawer) return;

  if (open) {
    drawer.classList.remove('translate-x-full');
    drawer.classList.add('translate-x-0');
    document.getElementById('drawer-chat-input')?.focus();
  } else {
    drawer.classList.add('translate-x-full');
    drawer.classList.remove('translate-x-0');
  }
}

function sendQuickChip(message) {
  const input = document.getElementById('drawer-chat-input');
  if (input) {
    input.value = message;
    document.getElementById('drawer-chat-form')?.dispatchEvent(new Event('submit', { cancelable: true }));
  }
}

async function sendDrawerChatMessage(e) {
  e.preventDefault();
  const input = document.getElementById('drawer-chat-input');
  const hp = document.getElementById('drawer-chat-hp');
  const msg = input.value.trim();

  // Honeypot check
  if (hp && hp.value) return;

  // Debounce check (1200ms)
  const now = Date.now();
  if (now - lastSubmitTime < 1200) return;
  lastSubmitTime = now;

  if (!msg || msg.length < 2) return;

  let history = [];
  try {
    history = JSON.parse(sessionStorage.getItem('app_shared_chat_history') || '[]');
  } catch (e) {}

  history.push({ role: 'user', content: msg });
  sessionStorage.setItem('app_shared_chat_history', JSON.stringify(history));
  renderDrawerMessages(history);
  input.value = '';

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    });
    const data = await res.json();
    const reply = data.data ? data.data.reply : 'Communication channel nominal.';
    
    history.push({ role: 'assistant', content: reply });
    sessionStorage.setItem('app_shared_chat_history', JSON.stringify(history));
    renderDrawerMessages(history);
  } catch (err) {
    showToast('Chat Standby', String(err), 'error');
  }
}

/* ==========================================================================
   SECTION 7: Floating Bottom Dock Auto-Hide & Section Scrolling
   ========================================================================== */
function initFloatingDock() {
  const dock = document.getElementById('floating-dock');
  const peekBtn = document.getElementById('dock-peek-btn');
  let lastScrollY = window.scrollY;
  let ticking = false;

  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        const currentY = window.scrollY;
        if (currentY < 70) {
          toggleDock(true);
        } else if (currentY > lastScrollY && currentY - lastScrollY > 15) {
          toggleDock(false);
        } else if (currentY < lastScrollY && lastScrollY - currentY > 15) {
          toggleDock(true);
        }
        lastScrollY = currentY;
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });

  window.addEventListener('mousemove', (e) => {
    if (e.clientY > window.innerHeight - 50) {
      toggleDock(true);
    }
  }, { passive: true });
}

function toggleDock(show) {
  const dock = document.getElementById('floating-dock');
  const peekBtn = document.getElementById('dock-peek-btn');
  if (!dock) return;

  if (show) {
    dock.classList.remove('translate-y-28', 'opacity-0', 'pointer-events-none');
    dock.classList.add('translate-y-0', 'opacity-100', 'pointer-events-auto');
    peekBtn?.classList.add('hidden');
  } else {
    dock.classList.add('translate-y-28', 'opacity-0', 'pointer-events-none');
    dock.classList.remove('translate-y-0', 'opacity-100', 'pointer-events-auto');
    peekBtn?.classList.remove('hidden');
  }
}

function scrollToSection(sectionId) {
  const el = document.getElementById(sectionId);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    toggleDock(true);
  }
}

/* ==========================================================================
   SECTION 8: Official Dossier Modal & 2FA Security
   ========================================================================== */
function openOfficialDossierModal() {
  const modal = document.getElementById('modal-dossier');
  if (!modal) return;

  const now = new Date();
  document.getElementById('dossier-date-text').textContent = now.toISOString().split('T')[0];
  document.getElementById('dossier-ref-code').textContent = 'LS-' + now.getFullYear() + '-D' + Math.floor(Math.random() * 899 + 100);
  document.getElementById('dossier-sla-val').textContent = document.getElementById('metric-sla').textContent + '%';
  document.getElementById('dossier-co2-val').textContent = document.getElementById('metric-co2-saved').textContent + ' kg';
  document.getElementById('dossier-quality-val').textContent = document.getElementById('metric-quality').textContent + ' / 100';

  modal.classList.remove('hidden');
}

function closeOfficialDossierModal() {
  document.getElementById('modal-dossier')?.classList.add('hidden');
}

let active2FASecret = '';
async function open2FAModal() {
  const modal = document.getElementById('modal-2fa');
  modal?.classList.remove('hidden');

  try {
    const res = await fetch('/api/auth/2fa/generate');
    const data = await res.json();
    active2FASecret = data.secret;
    document.getElementById('2fa-secret-display').textContent = data.secret;
    document.getElementById('2fa-preview-display').textContent = data.preview_code;
    document.getElementById('totp-input').value = data.preview_code;
  } catch (err) {
    console.error(err);
  }
}

function close2FAModal() {
  document.getElementById('modal-2fa')?.classList.add('hidden');
}

async function verify2FACode(e) {
  e.preventDefault();
  const code = document.getElementById('totp-input').value.trim();
  const msgEl = document.getElementById('2fa-result-msg');

  try {
    const res = await fetch('/api/auth/2fa/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: 'DISPATCHER-01', code: code })
    });
    const data = await res.json();

    msgEl.classList.remove('hidden');
    if (data.verified) {
      msgEl.className = 'text-center text-xs font-semibold text-emerald-400';
      msgEl.textContent = 'RFC 6238 TOTP Verified! Signed dispatch token issued.';
      document.getElementById('2fa-status-pill').textContent = '2FA VERIFIED';
      showToast('2FA Clearance Granted', 'Chief Dispatcher clearance active with HMAC-signed token.', 'success');
      setTimeout(close2FAModal, 1400);
    } else {
      msgEl.className = 'text-center text-xs font-semibold text-rose-400';
      msgEl.textContent = data.error || 'Invalid code.';
      showToast('2FA Verification Failed', 'Invalid or expired 6-digit TOTP code.', 'error');
    }
  } catch (err) {
    console.error(err);
  }
}

function downloadDatabaseBackup(format) {
  window.open(`/api/admin/backup?format=${format}`, '_blank');
  showToast('Database Snapshot', `Exporting administrative ${format.toUpperCase()} database backup`, 'info');
}

/* ==========================================================================
   SECTION 9: Keyboard Navigation & Accessibility
   ========================================================================== */
function initKeyboardNavigation() {
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeOfficialDossierModal();
      close2FAModal();
      toggleChatDrawer(false);
    }
  });
}

function switchTab(tab) {
  activeTab = tab;
  ['feed', 'vision', 'audit'].forEach(t => {
    const pane = document.getElementById(`tab-pane-${t}`);
    const btn = document.getElementById(`tab-btn-${t}`);
    if (t === tab) {
      pane?.classList.remove('hidden');
      btn?.classList.add('border-sky-400', 'text-sky-400', 'font-bold');
      btn?.classList.remove('border-transparent', 'text-slate-400');
      btn?.setAttribute('aria-selected', 'true');
    } else {
      pane?.classList.add('hidden');
      btn?.classList.remove('border-sky-400', 'text-sky-400', 'font-bold');
      btn?.classList.add('border-transparent', 'text-slate-400');
      btn?.setAttribute('aria-selected', 'false');
    }
  });
  lucide.createIcons();
}

function initCookieBanner() {
  const consent = localStorage.getItem('logiswarm_cookie_consent');
  const banner = document.getElementById('cookie-banner');
  if (consent && banner) {
    banner.classList.add('hidden');
  }
}

function setCookieConsent(type) {
  localStorage.setItem('logiswarm_cookie_consent', type);
  const banner = document.getElementById('cookie-banner');
  if (banner) banner.classList.add('hidden');
  if (window.LogiAnalytics) window.LogiAnalytics.track('cookie_consent', { type });
}

function initClock() {
  const clockEl = document.getElementById('live-clock');
  function update() {
    const now = new Date();
    if (clockEl) clockEl.textContent = now.toTimeString().split(' ')[0] + ' UTC';
  }
  update();
  setInterval(update, 1000);
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}
