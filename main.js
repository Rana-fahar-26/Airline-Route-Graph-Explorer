/* ═══════════════════════════════════════════════════════════════
   AeroGraph — main.js
   D3 force graph · Map view · Pathfinder · Search
═══════════════════════════════════════════════════════════════ */

/* ── State ─────────────────────────────────────────────────── */
const state = {
  graphData:    { nodes: [], edges: [] },
  pathData:     null,
  selectedNode: null,
  pathMode:     "hops",
  viewMode:     "graph",
  fromIATA:     null,
  toIATA:       null,
  simulation:   null,
};

/* ── D3 Setup ──────────────────────────────────────────────── */
const svg       = d3.select("#graph-svg");
const root      = svg.select("#graph-root");
const width     = () => svg.node().clientWidth;
const height    = () => svg.node().clientHeight;

let transform = d3.zoomIdentity;
const zoom = d3.zoom()
  .scaleExtent([0.1, 8])
  .on("zoom", (e) => { transform = e.transform; root.attr("transform", transform); });
svg.call(zoom);

/* ── Starfield ─────────────────────────────────────────────── */
(function initStarfield() {
  const canvas = document.getElementById("starfield");
  const ctx    = canvas.getContext("2d");
  let stars    = [];

  function resize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    stars = Array.from({ length: 220 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 1.2,
      a: Math.random(),
      s: Math.random() * 0.003 + 0.001,
    }));
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const s of stars) {
      s.a += s.s;
      if (s.a > 1) s.s = -s.s;
      if (s.a < 0) s.s = -s.s;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(160,200,255,${s.a * 0.6})`;
      ctx.fill();
    }
    requestAnimationFrame(draw);
  }

  resize();
  window.addEventListener("resize", resize);
  draw();
})();

/* ── API Helpers ───────────────────────────────────────────── */
async function apiFetch(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json();
}

function showLoading(msg = "Computing…") {
  const ov = document.getElementById("loading-overlay");
  ov.querySelector(".loading-text").textContent = msg;
  ov.hidden = false;
}
function hideLoading() { document.getElementById("loading-overlay").hidden = true; }

function toast(msg, ms = 3000) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { el.hidden = true; }, ms);
}

/* ── Stats ─────────────────────────────────────────────────── */
async function loadStats() {
  try {
    const data = await apiFetch("/api/stats");
    const fmt = n => n >= 1000 ? (n/1000).toFixed(1)+"k" : String(n);
    document.getElementById("stat-airports").textContent  = fmt(data.airports);
    document.getElementById("stat-routes").textContent    = fmt(data.routes);
    document.getElementById("stat-airlines").textContent  = fmt(data.airlines);
    document.getElementById("an-airports").textContent    = fmt(data.airports);
    document.getElementById("an-routes").textContent      = fmt(data.routes);
    document.getElementById("an-airlines").textContent    = fmt(data.airlines);
    document.getElementById("an-nodes").textContent       = fmt(data.graph_nodes);
    document.getElementById("an-edges").textContent       = fmt(data.graph_edges);
  } catch(e) {
    console.warn("Stats unavailable:", e.message);
  }
}

/* ── Navigation ────────────────────────────────────────────── */
document.querySelectorAll(".nav-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const panelId = "panel-" + btn.dataset.panel;
    document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
    document.getElementById(panelId).classList.add("active");
  });
});

/* ── View Toggle ───────────────────────────────────────────── */
document.getElementById("btn-graph-view").addEventListener("click", () => switchView("graph"));
document.getElementById("btn-map-view").addEventListener("click",   () => switchView("map"));

function switchView(mode) {
  state.viewMode = mode;
  document.getElementById("graph-view").classList.toggle("active", mode === "graph");
  document.getElementById("map-view").classList.toggle("active",   mode === "map");
  document.getElementById("btn-graph-view").classList.toggle("active", mode === "graph");
  document.getElementById("btn-map-view").classList.toggle("active",   mode === "map");
  if (mode === "map" && state.graphData.nodes.length) renderMap();
}

/* ── Reset Zoom ────────────────────────────────────────────── */
document.getElementById("btn-reset-zoom").addEventListener("click", () => {
  svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity);
});

/* ── Sample Hubs ───────────────────────────────────────────── */
document.getElementById("btn-load-sample").addEventListener("click", async () => {
  showLoading("Loading hub network…");
  try {
    const data = await apiFetch("/api/graph/sample");
    if (!data.nodes.length) { toast("No data returned — is the backend running?"); return; }
    renderGraph(data.nodes, data.edges, null);
    document.getElementById("graph-empty").style.display = "none";
    toast(`Loaded ${data.nodes.length} hubs · ${data.edges.length} routes`);
  } catch(e) {
    toast("Backend unavailable — showing demo graph");
    renderDemoGraph();
  } finally { hideLoading(); }
});

/* ── Demo Graph (offline fallback) ────────────────────────── */
function renderDemoGraph() {
  const nodes = [
    {iata:"LHR", name:"London Heathrow", city:"London", country:"UK", lat:51.5, lon:-0.45},
    {iata:"JFK", name:"John F. Kennedy", city:"New York", country:"US", lat:40.6, lon:-73.8},
    {iata:"DXB", name:"Dubai International", city:"Dubai", country:"UAE", lat:25.2, lon:55.4},
    {iata:"SIN", name:"Singapore Changi", city:"Singapore", country:"SG", lat:1.36, lon:103.9},
    {iata:"CDG", name:"Charles de Gaulle", city:"Paris", country:"FR", lat:49.0, lon:2.55},
    {iata:"FRA", name:"Frankfurt Airport", city:"Frankfurt", country:"DE", lat:50.0, lon:8.57},
    {iata:"HKG", name:"Hong Kong Int'l", city:"Hong Kong", country:"HK", lat:22.3, lon:113.9},
    {iata:"LAX", name:"Los Angeles Int'l", city:"Los Angeles", country:"US", lat:33.9, lon:-118.4},
    {iata:"NRT", name:"Narita International", city:"Tokyo", country:"JP", lat:35.8, lon:140.4},
    {iata:"SYD", name:"Sydney Airport", city:"Sydney", country:"AU", lat:-33.9, lon:151.2},
  ];
  const pairs = ["LHR-JFK","LHR-DXB","LHR-CDG","LHR-FRA","JFK-LAX","DXB-SIN","DXB-HKG",
                 "SIN-HKG","SIN-SYD","FRA-DXB","FRA-JFK","CDG-JFK","HKG-NRT","LAX-NRT","NRT-SYD","LHR-SIN"];
  const edges = pairs.flatMap(p => {
    const [a,b] = p.split("-");
    return [{source:a, target:b}, {source:b, target:a}];
  });
  renderGraph(nodes, edges, null);
  document.getElementById("graph-empty").style.display = "none";
  toast("Demo graph loaded (backend offline)");
}

/* ── D3 Force Graph ────────────────────────────────────────── */
function renderGraph(nodes, edges, pathEdges) {
  // Stop previous simulation
  if (state.simulation) state.simulation.stop();

  root.selectAll("*").remove();

  const nodeMap = new Map(nodes.map(n => [n.iata, { ...n, id: n.iata }]));

  // Resolve edge endpoints
  const links = edges
    .map(e => ({
      source: nodeMap.get(e.source || e.from) || e.source,
      target: nodeMap.get(e.target || e.to)   || e.target,
      isPath: pathEdges ? pathEdges.some(p => (p.from===e.source||p.from===e.from) && (p.to===e.target||p.to===e.to)) : false,
    }))
    .filter(e => e.source && e.target && typeof e.source === "object" && typeof e.target === "object");

  const linkSel = root.append("g").attr("class","links")
    .selectAll("line").data(links).join("line")
    .attr("class", d => "link" + (d.isPath ? " path-edge" : ""));

  const nodeSel = root.append("g").attr("class","nodes")
    .selectAll("g").data([...nodeMap.values()]).join("g")
    .attr("class", d => {
      let c = "node";
      if (pathEdges) {
        const inPath = pathEdges.some(p => p.from === d.iata || p.to === d.iata);
        if (inPath) c += " path-node";
      }
      return c;
    })
    .call(d3.drag()
      .on("start", (e,d) => { if(!e.active) sim.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; })
      .on("drag",  (e,d) => { d.fx=e.x; d.fy=e.y; })
      .on("end",   (e,d) => { if(!e.active) sim.alphaTarget(0); d.fx=null; d.fy=null; })
    )
    .on("mouseover", showNodeTooltip)
    .on("mousemove", moveNodeTooltip)
    .on("mouseout",  hideNodeTooltip)
    .on("click",     onNodeClick);

  nodeSel.append("circle").attr("r", d => {
    const degree = links.filter(l => l.source.iata===d.iata||l.target.iata===d.iata).length;
    return Math.max(4, Math.min(14, 4 + Math.sqrt(degree) * 1.8));
  });

  nodeSel.append("text").attr("dy", 18).text(d => d.iata);

  const sim = d3.forceSimulation([...nodeMap.values()])
    .force("link",    d3.forceLink(links).id(d=>d.iata).distance(100).strength(0.4))
    .force("charge",  d3.forceManyBody().strength(-200))
    .force("center",  d3.forceCenter(width()/2, height()/2))
    .force("collide", d3.forceCollide(20))
    .on("tick", () => {
      linkSel
        .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
      nodeSel.attr("transform", d => `translate(${d.x},${d.y})`);
    });

  state.simulation = sim;
  state.graphData  = { nodes: [...nodeMap.values()], edges: links };
}

function showNodeTooltip(e, d) {
  const tt = document.getElementById("node-tooltip");
  tt.querySelector(".tt-iata").textContent = d.iata;
  tt.querySelector(".tt-name").textContent = d.name || "—";
  tt.querySelector(".tt-loc").textContent  = [d.city, d.country].filter(Boolean).join(", ");
  tt.hidden = false;
  moveNodeTooltip(e);
}
function moveNodeTooltip(e) {
  const tt = document.getElementById("node-tooltip");
  tt.style.left = (e.clientX + 14) + "px";
  tt.style.top  = (e.clientY - 10) + "px";
}
function hideNodeTooltip()  { document.getElementById("node-tooltip").hidden = true; }

async function onNodeClick(e, d) {
  state.selectedNode = d.iata;
  // pre-fill search
  document.getElementById("airport-search").value = `${d.iata} — ${d.name}`;
  await loadAirportInfo(d.iata);
}

/* ── Map View ──────────────────────────────────────────────── */
function renderMap() {
  const mapSvg = document.getElementById("map-svg");
  const routeG = document.getElementById("map-routes");
  const apG    = document.getElementById("map-airports");
  routeG.innerHTML = "";
  apG.innerHTML    = "";

  const W = 1000, H = 500;
  function project(lat, lon) {
    const x = (lon + 180) / 360 * W;
    const y = (90  - lat) / 180 * H;
    return [x, y];
  }

  // Draw edges
  for (const e of state.graphData.edges) {
    const s = e.source, t = e.target;
    if (!s?.lat || !t?.lat) continue;
    const [sx, sy] = project(s.lat, s.lon);
    const [tx, ty] = project(t.lat, t.lon);
    const line = document.createElementNS("http://www.w3.org/2000/svg","path");
    // Great-circle arc approximation via quadratic bezier
    const mx = (sx+tx)/2, my = (sy+ty)/2 - 30;
    line.setAttribute("d", `M${sx},${sy} Q${mx},${my} ${tx},${ty}`);
    line.setAttribute("class", "map-route" + (e.isPath ? " path-route" : ""));
    routeG.appendChild(line);
  }

  // Draw nodes
  for (const n of state.graphData.nodes) {
    if (!n.lat) continue;
    const [x, y] = project(n.lat, n.lon);
    const circle = document.createElementNS("http://www.w3.org/2000/svg","circle");
    circle.setAttribute("cx", x); circle.setAttribute("cy", y); circle.setAttribute("r", 3);
    circle.setAttribute("class", "map-airport");
    circle.setAttribute("data-iata", n.iata);

    circle.addEventListener("mouseenter", (ev) => {
      const tt = document.getElementById("map-tooltip");
      tt.textContent = `${n.iata} — ${n.name}`;
      tt.style.left = (ev.clientX - 300 + 10) + "px";
      tt.style.top  = (ev.clientY - 58  - 10) + "px";
      tt.hidden = false;
    });
    circle.addEventListener("mouseleave", () => {
      document.getElementById("map-tooltip").hidden = true;
    });
    apG.appendChild(circle);
  }
}

/* ── Airport Search ────────────────────────────────────────── */
function setupSearch(inputId, resultsId, onSelect) {
  const input   = document.getElementById(inputId);
  const results = document.getElementById(resultsId);
  let debounce;

  input.addEventListener("input", () => {
    clearTimeout(debounce);
    const q = input.value.trim();
    if (q.length < 2) { results.hidden = true; return; }
    debounce = setTimeout(async () => {
      try {
        const data = await apiFetch(`/api/airports/search?q=${encodeURIComponent(q)}&limit=8`);
        renderDropdown(results, data, (ap) => {
          input.value   = `${ap.iata} — ${ap.name}`;
          results.hidden = true;
          onSelect(ap);
        });
      } catch(e) {
        results.hidden = true;
      }
    }, 250);
  });

  document.addEventListener("click", (e) => {
    if (!input.contains(e.target) && !results.contains(e.target)) results.hidden = true;
  });
}

function renderDropdown(ul, airports, onSelect) {
  ul.innerHTML = "";
  if (!airports.length) { ul.hidden = true; return; }
  for (const ap of airports) {
    const li = document.createElement("li");
    li.innerHTML = `
      <span class="drop-iata">${ap.iata}</span>
      <div class="drop-info">
        <div class="drop-name">${ap.name}</div>
        <div class="drop-city">${ap.city}, ${ap.country}</div>
      </div>`;
    li.addEventListener("click", () => onSelect(ap));
    ul.appendChild(li);
  }
  ul.hidden = false;
}

/* ── Main Airport Search (Explorer panel) ──────────────────── */
setupSearch("airport-search", "search-results", async (ap) => {
  await loadAirportInfo(ap.iata);
});

async function loadAirportInfo(iata) {
  showLoading("Loading airport data…");
  try {
    const [ap, conn] = await Promise.all([
      apiFetch(`/api/airports/${iata}`),
      apiFetch(`/api/connectivity/${iata}`).catch(() => null),
    ]);

    // Fill card
    document.getElementById("info-iata").textContent     = ap.iata;
    document.getElementById("info-name").textContent     = ap.name;
    document.getElementById("info-location").textContent = `${ap.city}, ${ap.country}`;
    document.getElementById("info-lat").textContent      = ap.lat?.toFixed(4) ?? "—";
    document.getElementById("info-lon").textContent      = ap.lon?.toFixed(4) ?? "—";
    document.getElementById("info-icao").textContent     = ap.icao || "—";
    document.getElementById("info-tz").textContent       = ap.timezone || ap.tz || "—";
    if (conn) {
      document.getElementById("conn-out").textContent   = conn.out_degree ?? "—";
      document.getElementById("conn-in").textContent    = conn.in_degree  ?? "—";
      document.getElementById("conn-reach").textContent = conn.reachable_2hops ?? "—";
    }
    document.getElementById("airport-info").hidden = false;

  } catch(e) {
    toast("Airport not found");
  } finally { hideLoading(); }
}

document.getElementById("btn-show-routes").addEventListener("click", async () => {
  const iataEl = document.getElementById("info-iata");
  const iata = iataEl.textContent;
  if (!iata || iata === "JFK" && !document.getElementById("airport-info").hidden === false) return;
  showLoading("Fetching routes…");
  try {
    const data = await apiFetch(`/api/routes/${iata}`);
    renderRouteList(data.routes);
    buildGraphFromRoutes(data.source, data.routes);
  } catch(e) {
    toast("Could not load routes — is the backend running?");
  } finally { hideLoading(); }
});

function renderRouteList(routes) {
  const section = document.getElementById("routes-section");
  const ul      = document.getElementById("routes-list");
  document.getElementById("route-count").textContent = routes.length;
  ul.innerHTML = "";
  for (const r of routes.slice(0, 40)) {
    const li = document.createElement("li");
    li.className = "route-item";
    li.innerHTML = `
      <span class="route-iata">${r.destination}</span>
      <span class="route-city">${r.dest_city || "—"}, ${r.dest_country || ""}</span>
      <span class="route-airline">${r.airline || ""}</span>`;
    ul.appendChild(li);
  }
  section.hidden = false;
}

function buildGraphFromRoutes(source, routes) {
  if (!source) return;
  const nodes = [source, ...routes.map(r => ({
    iata: r.destination, name: r.dest_name, city: r.dest_city, country: r.dest_country,
    lat: r.dest_lat, lon: r.dest_lon
  }))];
  const edges = routes.map(r => ({ source: source.iata, target: r.destination }));
  renderGraph(nodes, edges, null);
  document.getElementById("graph-empty").style.display = "none";
  if (state.viewMode === "map") renderMap();
}

/* ── Pathfinder ────────────────────────────────────────────── */
let fromAP = null, toAP = null;

setupSearch("path-from", "path-from-results", (ap) => { fromAP = ap; state.fromIATA = ap.iata; });
setupSearch("path-to",   "path-to-results",   (ap) => { toAP   = ap; state.toIATA   = ap.iata; });

// Mode toggle
document.querySelectorAll(".toggle-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".toggle-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    state.pathMode = btn.dataset.mode;
  });
});

// Swap
document.getElementById("btn-swap").addEventListener("click", () => {
  [fromAP, toAP] = [toAP, fromAP];
  [state.fromIATA, state.toIATA] = [state.toIATA, state.fromIATA];
  const fi = document.getElementById("path-from"), ti = document.getElementById("path-to");
  [fi.value, ti.value] = [ti.value, fi.value];
});

document.getElementById("btn-find-path").addEventListener("click", async () => {
  const src = state.fromIATA;
  const dst = state.toIATA;
  if (!src || !dst) { toast("Please select both airports"); return; }
  if (src === dst)  { toast("Source and destination are the same"); return; }

  showLoading("Finding shortest path…");
  document.getElementById("path-result").hidden    = true;
  document.getElementById("path-no-result").hidden = true;

  try {
    const data = await apiFetch(`/api/shortest-path?from=${src}&to=${dst}&mode=${state.pathMode}`);

    if (!data.found) {
      document.getElementById("path-no-result").hidden = false;
      return;
    }

    document.getElementById("path-hops").textContent = data.hops;
    document.getElementById("path-dist").textContent = data.total_distance_km ? data.total_distance_km+"km" : "—";

    const stopsList = document.getElementById("path-stops");
    stopsList.innerHTML = "";
    data.stops.forEach((s, i) => {
      const li = document.createElement("li");
      li.className = "path-stop";
      li.style.animationDelay = (i * 60) + "ms";
      li.innerHTML = `
        <span class="ps-num">${i+1}</span>
        <span class="ps-iata">${s.iata}</span>
        <div class="ps-info">
          <div class="ps-name">${s.name || "—"}</div>
          <div class="ps-city">${[s.city, s.country].filter(Boolean).join(", ")}</div>
        </div>
        ${i < data.stops.length-1 ? '<span class="ps-arrow">→</span>' : ''}`;
      stopsList.appendChild(li);
    });

    document.getElementById("path-result").hidden = false;

    // Render path on graph
    renderGraph(data.stops, data.edges.map(e=>({source:e.from,target:e.to})), data.edges);
    document.getElementById("graph-empty").style.display = "none";
    if (state.viewMode === "map") renderMap();

  } catch(e) {
    toast("Path calculation failed — check backend connection");
  } finally { hideLoading(); }
});

/* ── Hub Tags (Analytics panel) ───────────────────────────── */
document.querySelectorAll(".hub-tag").forEach(tag => {
  tag.addEventListener("click", async () => {
    const iata = tag.textContent.split("—")[0].trim();
    document.getElementById("airport-search").value = iata;
    // Switch to explorer
    document.querySelectorAll(".nav-btn")[0].click();
    await loadAirportInfo(iata);
  });
});

/* ── Init ──────────────────────────────────────────────────── */
loadStats();

// Attempt to load sample on startup after brief delay
setTimeout(async () => {
  try {
    const data = await apiFetch("/api/graph/sample");
    if (data.nodes.length) {
      renderGraph(data.nodes, data.edges, null);
      document.getElementById("graph-empty").style.display = "none";
    }
  } catch {
    // Backend not running — that's fine, user sees empty hint
  }
}, 800);
