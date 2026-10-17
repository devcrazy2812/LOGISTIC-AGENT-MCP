// State & Map Globals
let map;
let routeLayers = [];
let markerLayers = [];
let hazardLayers = [];
let activeTab = 'feed';

const vehicleColors = {
  'FLEET-EV-01': '#10b981',    // Emerald Green (Electric)
  'FLEET-TRK-02': '#6366f1',   // Indigo (Diesel)
  'FLEET-MID-03': '#f59e0b',   // Amber (CNG)
  'FLEET-COLD-04': '#06b6d4'   // Cyan (Hybrid Reefer)
};

const agentBadges = {
  'Commander-Prime': { color: 'bg-blue-950 border-blue-800 text-blue-300', icon: 'shield' },
  'Sentinel-Risk': { color: 'bg-red-950 border-red-800 text-red-300', icon: 'alert-triangle' },
  'StockMaster': { color: 'bg-purple-950 border-purple-800 text-purple-300', icon: 'package' },
  'RouteOptima': { color: 'bg-emerald-950 border-emerald-800 text-emerald-300', icon: 'navigation' },
  'CommLiaison': { color: 'bg-amber-950 border-amber-800 text-amber-300', icon: 'message-square' },
  'QualityGuard': { color: 'bg-pink-950 border-pink-800 text-pink-300', icon: 'award' }
};

document.addEventListener('DOMContentLoaded', () => {
  initMap();
  initClock();
  initEventListeners();
  fetchState();
  setInterval(fetchState, 4000);
});

function initClock() {
  const clockEl = document.getElementById('live-clock');
  function update() {
    const now = new Date();
    if (clockEl) {
      clockEl.textContent = now.toTimeString().split(' ')[0] + ' UTC';
    }
  }
  update();
  setInterval(update, 1000);
}

function initMap() {
  map = L.map('map', {
    zoomControl: true,
    attributionControl: false
  }).setView([19.0760, 72.8777], 11);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18
  }).addTo(map);
}

function initEventListeners() {
  document.getElementById('btn-reoptimize')?.addEventListener('click', async () => {
    showStatusBadge('OPTIMIZING SWARM (FEEDBACK LOOP)...', 'bg-blue-900 border-blue-700 text-blue-300');
    try {
      const res = await fetch('/api/optimize', { method: 'POST' });
      const data = await res.json();
      renderState(data.data);
      showStatusBadge('OPTIMIZATION COMPLETE', 'bg-emerald-950 border-emerald-800 text-emerald-400');
    } catch (err) {
      console.error(err);
    }
  });

  document.getElementById('btn-reset')?.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/reset', { method: 'POST' });
      const data = await res.json();
      renderState(data.data);
      showStatusBadge('SWARM NOMINAL', 'bg-gray-800 border-gray-700 text-emerald-400');
    } catch (err) {
      console.error(err);
    }
  });

  document.getElementById('btn-export')?.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/export');
      const text = await res.text();
      document.getElementById('report-content').textContent = text;
      document.getElementById('modal-report').classList.remove('hidden');
    } catch (err) {
      console.error(err);
    }
  });

  document.getElementById('modal-close')?.addEventListener('click', () => {
    document.getElementById('modal-report').classList.add('hidden');
  });

  document.getElementById('btn-copy-report')?.addEventListener('click', () => {
    const text = document.getElementById('report-content').textContent;
    navigator.clipboard.writeText(text);
    alert('Mission Audit Report copied to clipboard!');
  });
}

function switchTab(tab) {
  activeTab = tab;
  ['feed', 'chat', 'vision'].forEach(t => {
    const pane = document.getElementById(`tab-pane-${t}`);
    const btn = document.getElementById(`tab-btn-${t}`);
    if (t === tab) {
      pane?.classList.remove('hidden');
      btn?.classList.add('border-cyan-400', 'text-cyan-400', 'font-bold');
      btn?.classList.remove('border-transparent', 'text-slate-400');
    } else {
      pane?.classList.add('hidden');
      btn?.classList.remove('border-cyan-400', 'text-cyan-400', 'font-bold');
      btn?.classList.add('border-transparent', 'text-slate-400');
    }
  });
  lucide.createIcons();
}

async function sendChatMessage(e) {
  e.preventDefault();
  const input = document.getElementById('chat-input');
  const msg = input.value.trim();
  if (!msg) return;

  const chatContainer = document.getElementById('chat-messages');
  chatContainer.innerHTML += `
    <div class="p-2 rounded bg-cyan-950/40 border border-cyan-900/40 text-slate-200">
      <b class="text-slate-300">Dispatcher:</b> ${msg}
    </div>
  `;
  input.value = '';
  chatContainer.scrollTop = chatContainer.scrollHeight;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    });
    const data = await res.json();
    const reply = data.data.reply;
    chatContainer.innerHTML += `
      <div class="p-2 rounded bg-gray-800/60 text-slate-300">
        <b class="text-cyan-400">Commander-Prime:</b> ${reply}
      </div>
    `;
    chatContainer.scrollTop = chatContainer.scrollHeight;
  } catch (err) {
    console.error(err);
  }
}

async function runSampleMultimodalInspection() {
  const resultBox = document.getElementById('vision-result-box');
  resultBox.textContent = "Analyzing cargo imagery via Google Gemini Multimodal Vision API...";
  
  try {
    const res = await fetch('/api/inspect_cargo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_base64: "SAMPLE_MOCK_BASE64_DATA"
      })
    });
    const data = await res.json();
    resultBox.textContent = JSON.stringify(data.data, null, 2);
  } catch (err) {
    resultBox.textContent = `Error: ${err}`;
  }
}

async function submitHumanFeedback(rating) {
  const comments = {
    'positive': 'Optimal route plan approved by Human Dispatcher.',
    'rebalance': 'Human request: Prioritize EV allocation for upcoming legs.',
    'negative': 'Flagged sub-optimal stop sequence. Requested recalculation.'
  };
  try {
    const res = await fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating, comment: comments[rating] })
    });
    showStatusBadge('FEEDBACK RECORDED BY SWARM', 'bg-pink-950 border-pink-800 text-pink-300');
    setTimeout(() => {
      showStatusBadge('SWARM NOMINAL', 'bg-gray-800 border-gray-700 text-emerald-400');
    }, 2000);
  } catch (err) {
    console.error(err);
  }
}

function showStatusBadge(text, classes) {
  const el = document.getElementById('swarm-status-text');
  if (el) {
    el.textContent = text;
  }
}

async function fetchState() {
  try {
    const res = await fetch('/api/state');
    if (!res.ok) return;
    const state = await res.json();
    renderState(state);
  } catch (err) {
    console.error('Failed to fetch state:', err);
  }
}

async function injectDisruption(type) {
  showStatusBadge('CRISIS INJECTED - HEALING...', 'bg-red-950 border-red-800 text-red-400 animate-pulse');
  try {
    const res = await fetch('/api/disruption', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type })
    });
    const data = await res.json();
    renderState(data.data);
    setTimeout(() => {
      showStatusBadge('SWARM RE-STABILIZED', 'bg-emerald-950 border-emerald-800 text-emerald-400');
    }, 1500);
  } catch (err) {
    console.error(err);
  }
}

function renderState(state) {
  if (!state) return;

  // 1. Render Metrics
  const m = state.metrics || {};
  const fb = state.latest_feedback || {};

  document.getElementById('metric-sla').textContent = (m.sla_compliance_rate || 100.0).toFixed(1);
  document.getElementById('metric-quality').textContent = (fb.composite_score || 92.5).toFixed(1);
  document.getElementById('metric-cost').textContent = (m.total_cost_usd || 0.0).toLocaleString('en-US', { minimumFractionDigits: 2 });
  document.getElementById('metric-dist').textContent = (m.total_distance_km || 0.0).toFixed(1);
  document.getElementById('metric-co2-saved').textContent = (m.co2_saved_vs_baseline_kg || 0.0).toFixed(1);
  document.getElementById('metric-utilization').textContent = (m.fleet_utilization_rate || 0.0).toFixed(1);
  document.getElementById('metric-recoveries').textContent = m.autonomous_recovery_count || 0;

  // 2. Render Map Layers
  renderMap(state);

  // 3. Render Fleet Table
  renderFleetTable(state.vehicles || []);

  // 4. Render Agent Thoughts Feed
  renderThoughts(state.agent_thoughts || []);

  // 5. Render Notifications
  renderNotifications(state.notifications || []);
}

function renderMap(state) {
  routeLayers.forEach(l => map.removeLayer(l));
  markerLayers.forEach(l => map.removeLayer(l));
  hazardLayers.forEach(l => map.removeLayer(l));
  routeLayers = [];
  markerLayers = [];
  hazardLayers = [];

  // Draw Hazards
  (state.disruptions || []).forEach(d => {
    if (d.affected_lat && d.affected_lng && d.radius_km) {
      const circle = L.circle([d.affected_lat, d.affected_lng], {
        radius: d.radius_km * 1000,
        color: '#ef4444',
        fillColor: '#dc2626',
        fillOpacity: 0.25,
        weight: 2,
        dashArray: '6, 6'
      }).addTo(map);

      circle.bindPopup(`
        <div class="text-xs">
          <strong class="text-red-500 font-bold uppercase">Hazard Corridor</strong><br/>
          <strong>${d.title}</strong><br/>
          ${d.description}
        </div>
      `);
      hazardLayers.push(circle);
    }
  });

  // Draw Depots
  (state.depots || []).forEach(depot => {
    const icon = L.divIcon({
      className: 'custom-depot-marker',
      html: `
        <div class="w-8 h-8 rounded-lg bg-blue-600 border-2 border-white flex items-center justify-center shadow-lg text-white font-bold text-xs">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 32]
    });

    const marker = L.marker([depot.lat, depot.lng], { icon }).addTo(map);
    const stockList = Object.entries(depot.inventory || {})
      .map(([k, v]) => `• ${k.replace(/_/g, ' ')}: <b>${v}</b>`)
      .join('<br/>');

    marker.bindPopup(`
      <div class="text-xs">
        <strong class="text-blue-400 font-bold uppercase">${depot.id}</strong><br/>
        <span class="font-bold text-slate-800">${depot.name}</span><br/>
        <div class="mt-1 pt-1 border-t border-gray-200">
          <strong>Available Stock:</strong><br/>
          ${stockList}
        </div>
      </div>
    `);
    markerLayers.push(marker);
  });

  // Draw Orders
  (state.orders || []).forEach(ord => {
    let pinColor = '#10b981';
    if (ord.priority === 'CRITICAL') pinColor = '#ef4444';
    else if (ord.priority === 'HIGH') pinColor = '#f59e0b';
    if (ord.status === 'delayed') pinColor = '#dc2626';

    const icon = L.divIcon({
      className: 'custom-order-marker',
      html: `
        <div class="w-5 h-5 rounded-full border-2 border-white shadow flex items-center justify-center text-[10px] font-bold text-white" style="background-color: ${pinColor};">
          ${ord.priority[0]}
        </div>
      `,
      iconSize: [20, 20],
      iconAnchor: [10, 10]
    });

    const marker = L.marker([ord.lat, ord.lng], { icon }).addTo(map);
    marker.bindPopup(`
      <div class="text-xs">
        <strong class="text-slate-800 font-bold">${ord.customer}</strong> (${ord.id})<br/>
        <span>Cargo: ${ord.quantity}x ${ord.item} (${ord.weight_kg} kg)</span><br/>
        <span>Priority: <b style="color:${pinColor}">${ord.priority}</b></span><br/>
        <span>Status: <b>${ord.status.toUpperCase()}</b></span><br/>
        <span>Est. Arrival: <b>${ord.estimated_arrival_minutes ? ord.estimated_arrival_minutes + ' min' : 'Pending'}</b></span>
      </div>
    `);
    markerLayers.push(marker);
  });

  // Draw Routes
  (state.vehicles || []).forEach(v => {
    if (v.route_stops && v.route_stops.length > 1 && v.status !== 'disrupted') {
      const latlngs = v.route_stops.map(s => [s.lat, s.lng]);
      const color = vehicleColors[v.id] || '#3b82f6';

      const polyline = L.polyline(latlngs, {
        color: color,
        weight: 3.5,
        opacity: 0.85,
        dashArray: v.type.includes('EV') ? '4, 4' : null
      }).addTo(map);

      polyline.bindTooltip(`${v.name} (${v.assigned_orders.length} deliveries)`, {
        sticky: true
      });
      routeLayers.push(polyline);
    }
  });
}

function renderFleetTable(vehicles) {
  const tbody = document.getElementById('fleet-table-body');
  if (!tbody) return;

  tbody.innerHTML = vehicles.map(v => {
    const isDisrupted = v.status === 'disrupted';
    const statusBadge = isDisrupted
      ? `<span class="px-2 py-0.5 rounded-full bg-red-950 border border-red-800 text-red-400 font-bold">DISABLED</span>`
      : v.assigned_orders.length > 0
        ? `<span class="px-2 py-0.5 rounded-full bg-emerald-950 border border-emerald-800 text-emerald-400 font-semibold">EN ROUTE</span>`
        : `<span class="px-2 py-0.5 rounded-full bg-gray-800 text-slate-400 font-medium">IDLE</span>`;

    const colorDot = vehicleColors[v.id] || '#3b82f6';

    return `
      <tr class="hover:bg-gray-800/40 transition">
        <td class="py-2.5 px-3">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full" style="background-color: ${colorDot}"></span>
            <div>
              <div class="font-bold text-slate-200">${v.name}</div>
              <div class="text-[10px] text-slate-500 font-mono">${v.id}</div>
            </div>
          </div>
        </td>
        <td class="py-2.5 px-3">
          <div class="text-slate-300 font-medium">${v.type}</div>
          <div class="text-[10px] text-slate-400">${v.fuel_type} • ${v.capacity_kg} kg cap</div>
        </td>
        <td class="py-2.5 px-3">
          <span class="font-bold text-cyan-400">${v.assigned_orders.length}</span> orders
          <div class="text-[10px] text-slate-500 font-mono">${v.assigned_orders.join(', ') || 'None'}</div>
        </td>
        <td class="py-2.5 px-3">
          <div class="font-mono">${v.total_distance_km} km</div>
          <div class="text-[10px] text-slate-400 font-mono">${v.total_time_min} mins</div>
        </td>
        <td class="py-2.5 px-3">
          <div class="text-emerald-400 font-mono">$${v.total_cost_usd}</div>
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

  const recent = thoughts.slice(-25);

  container.innerHTML = recent.map(t => {
    const meta = agentBadges[t.agent_name] || { color: 'bg-gray-800 border-gray-700 text-slate-300', icon: 'bot' };
    
    let phaseColor = 'text-cyan-400';
    if (t.phase === 'OBSERVE') phaseColor = 'text-blue-400';
    else if (t.phase === 'REASON') phaseColor = 'text-purple-400';
    else if (t.phase === 'ACTION') phaseColor = 'text-emerald-400';

    const toolsTags = (t.tools_used || []).map(tool => 
      `<span class="px-1.5 py-0.5 rounded bg-gray-800 text-[9px] text-slate-400 border border-gray-700/60 font-mono">tool:${tool}</span>`
    ).join(' ');

    return `
      <div class="p-2.5 rounded-lg bg-gray-800/40 border border-gray-800 hover:border-gray-700 transition space-y-1">
        <div class="flex items-center justify-between text-[10px]">
          <span class="px-2 py-0.5 rounded border text-[10px] font-bold ${meta.color}">
            ${t.agent_name} (${t.role})
          </span>
          <span class="text-slate-500 font-mono">${t.timestamp}</span>
        </div>
        <div class="text-slate-300 leading-snug">
          <span class="font-bold ${phaseColor}">[${t.phase}]</span> ${t.content}
        </div>
        ${toolsTags ? `<div class="pt-1 flex flex-wrap gap-1">${toolsTags}</div>` : ''}
      </div>
    `;
  }).join('');

  container.scrollTop = container.scrollHeight;
}

function renderNotifications(notifications) {
  const box = document.getElementById('notifications-box');
  if (!box) return;

  if (!notifications.length) {
    box.innerHTML = `<span class="text-slate-500 italic">No crisis bulletins active. Routine dispatch clear.</span>`;
    return;
  }

  box.innerHTML = notifications.slice(-3).map(n => `
    <div class="p-1.5 rounded bg-amber-950/30 border border-amber-900/40 text-amber-200/90 leading-tight">
      ${n.message}
    </div>
  `).join('');
}
