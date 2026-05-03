# ✈ AeroGraph — Airline Route Graph Explorer

A production-grade web application that models **global airports as graph nodes** and **flight routes as edges**, enabling interactive exploration, connectivity analysis, and shortest-path computation over the OpenFlights dataset.

---

## 🏗 Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Frontend   | HTML5 · CSS3 · JavaScript ES6+      |
| Graph Viz  | D3.js v7 (force-directed graph)     |
| Backend    | Python 3.11 · Flask 3               |
| Raw Store  | MongoDB 7 (document collections)    |
| Graph DB   | Neo4j 5 (node/edge traversal)       |
| Packaging  | Docker · Docker Compose             |

---

## 📁 Project Structure

```
airline-route-explorer/
├── app.py                 # Flask REST API
├── setup_db.py            # Data loader (MongoDB + Neo4j)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── data/                  # OpenFlights .dat files (auto-downloaded)
│   ├── airports.dat
│   ├── routes.dat
│   └── airlines.dat
├── templates/
│   └── index.html         # Single-page interface
└── static/
    ├── css/style.css
    └── js/main.js
```

---

## 🚀 Quick Start

### Option A — Docker Compose (recommended)

```bash
# Clone or unzip the project
cd airline-route-explorer

# Start all services (MongoDB, Neo4j, Flask app)
docker-compose up --build
```

Open http://localhost:5000

> First run downloads the OpenFlights dataset, loads MongoDB, and builds the Neo4j graph (~2 min).

---

### Option B — Manual Setup

#### 1. Install dependencies

```bash
pip install -r requirements.txt
```

#### 2. Start MongoDB

```bash
# Install MongoDB Community and start
mongod --dbpath /data/db
```

#### 3. Start Neo4j

Download Neo4j Community Edition from https://neo4j.com/download/  
Set bolt password to `password` or update `.env`.

> **APOC Plugin** — For distance-based shortest paths, install the APOC plugin in Neo4j.

#### 4. Configure environment

```bash
cp .env.example .env
# Edit MONGO_URI, NEO4J_URI, NEO4J_USER, NEO4J_PASS as needed
```

#### 5. Load data

```bash
python setup_db.py
```

This will:
- Download `airports.dat`, `routes.dat`, `airlines.dat` from OpenFlights
- Parse and insert ~7,500 airports, ~67,000 routes into MongoDB
- Build Neo4j graph: Airport nodes + ROUTE relationships with haversine distances

#### 6. Run the server

```bash
python app.py
```

Open http://localhost:5000

---

## 🌐 API Reference

| Method | Endpoint                       | Description                          |
|--------|--------------------------------|--------------------------------------|
| GET    | `/api/stats`                   | Graph-level statistics               |
| GET    | `/api/airports/search?q=`      | Search airports by name/IATA/city    |
| GET    | `/api/airports/<IATA>`         | Single airport details               |
| GET    | `/api/routes/<IATA>`           | All outbound routes (Neo4j)          |
| GET    | `/api/shortest-path?from=&to=` | Shortest path (hops or distance)     |
| GET    | `/api/graph/sample`            | Sample hub subgraph for visualisation|
| GET    | `/api/connectivity/<IATA>`     | Degree + reachability metrics        |

### Example Requests

```bash
# Search airports
curl "http://localhost:5000/api/airports/search?q=dubai"

# Get routes from Dubai
curl "http://localhost:5000/api/routes/DXB"

# Shortest path: London → Singapore
curl "http://localhost:5000/api/shortest-path?from=LHR&to=SIN&mode=hops"
```

---

## 🗂 Data Model

### MongoDB Collections

**airports**
```json
{
  "iata": "LHR", "name": "London Heathrow",
  "city": "London", "country": "United Kingdom",
  "lat": 51.477500, "lon": -0.461389,
  "icao": "EGLL", "timezone": "Europe/London"
}
```

**routes**
```json
{
  "airline": "BA", "src_iata": "LHR", "dst_iata": "JFK",
  "stops": 0, "equipment": "777", "distance_km": 5540
}
```

**airlines**
```json
{
  "iata": "EK", "name": "Emirates",
  "country": "United Arab Emirates", "active": true
}
```

### Neo4j Graph Schema

```
(:Airport {iata, name, city, country, lat, lon})
  -[:ROUTE {airline, stops, distance, equipment}]->
(:Airport)
```

---

## 🎯 Features

- **Airport Search** — fuzzy search across name, city, country, IATA/ICAO codes
- **Route Explorer** — visualise all direct connections from any airport
- **Force Graph** — D3.js interactive network with drag, zoom, and tooltips
- **Map View** — geographic projection with great-circle arc routes
- **Shortest Path** — minimum hops OR minimum distance via Neo4j traversal
- **Connectivity Analytics** — in/out degree, 2-hop reachability
- **Global Hub Heatmap** — quick-jump to major hub airports

---

## 📊 Dataset

Source: [OpenFlights](https://openflights.org/data.html)

| File          | Records  | Description                     |
|---------------|----------|---------------------------------|
| airports.dat  | ~7,500   | Airport metadata + coordinates  |
| routes.dat    | ~67,000  | Airline routes (src → dst)      |
| airlines.dat  | ~5,888   | Airline names and codes         |

---

## 🛠 Graph Algorithms

| Algorithm       | Implementation           | Use Case               |
|-----------------|--------------------------|------------------------|
| BFS / Hop Count | Neo4j `shortestPath()`   | Min-transfer routing   |
| Dijkstra        | Neo4j APOC `dijkstra()`  | Min-distance routing   |
| Degree Analysis | Cypher aggregation       | Hub identification     |
| Reachability    | Cypher `*1..2` traversal | 2-hop reach count      |

---

## 👥 Team / Credits

Built with ❤️ using the OpenFlights open dataset.  
Graph processing powered by Neo4j · Data storage by MongoDB · Visualised with D3.js.
