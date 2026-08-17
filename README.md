# ✈️ AeroGraph — Airline Route Graph Explorer

> **Interactive graph analytics for global airline networks — built with Flask, MongoDB, Neo4j, and D3.js.**

AeroGraph transforms the OpenFlights dataset into an interactive graph of airports and airline routes. Explore global connectivity, inspect airport hubs, visualize route networks, and calculate shortest paths by **number of hops** or **distance**.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.x-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.x-008CC1?logo=neo4j&logoColor=white)](https://neo4j.com/)
[![D3.js](https://img.shields.io/badge/D3.js-v7-F9A03C?logo=d3.js&logoColor=white)](https://d3js.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

---

## 🚀 Why AeroGraph?

Airline networks are naturally represented as graphs: **airports are nodes** and **routes are edges**. AeroGraph combines a document database, graph database, REST API, and interactive visualization into one application for exploring that network.

### ✨ Highlights

- 🔎 **Airport Search** — find airports by name, city, country, IATA, or ICAO code
- 🕸️ **Interactive Force Graph** — explore route connectivity with D3.js
- 🗺️ **Geographic Route View** — inspect global connections spatially
- 🧭 **Shortest Path Analysis** — calculate minimum-hop or minimum-distance routes
- 📊 **Connectivity Analytics** — inspect degree and reachability metrics
- 🌍 **Global Hub Exploration** — quickly explore major international airports
- ⚡ **REST API** — programmatic access to airport, route, graph, and analytics data
- 🐳 **Dockerized Setup** — run the application and databases together with Docker Compose

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript ES6+ |
| Visualization | D3.js v7 |
| Backend | Python 3.11, Flask 3 |
| Document Database | MongoDB 7 |
| Graph Database | Neo4j 5 |
| Containers | Docker, Docker Compose |
| Data Source | OpenFlights |

---

## 🧠 Graph Algorithms

| Analysis | Approach | Purpose |
|---|---|---|
| BFS / Hop Count | Neo4j shortest-path traversal | Minimum-transfer routing |
| Dijkstra | Neo4j APOC | Minimum-distance routing |
| Degree Analysis | Cypher aggregation | Identify highly connected hubs |
| Reachability | Cypher `*1..2` traversal | Measure local network connectivity |

---

## 🏗️ Architecture

```text
                 ┌──────────────────────┐
                 │   Web UI / D3.js     │
                 └──────────┬───────────┘
                            │ HTTP / REST
                 ┌──────────▼───────────┐
                 │     Flask API        │
                 └──────┬────────┬──────┘
                        │        │
              ┌─────────▼───┐  ┌▼────────────┐
              │   MongoDB   │  │    Neo4j    │
              │ airport data│  │ route graph │
              └─────────────┘  └─────────────┘

                 OpenFlights Dataset
                         │
                         ▼
                   Data Loader
```

---

## 📁 Project Structure

```text
airline-route-explorer/
├── app.py                  # Flask REST API
├── setup_db.py             # OpenFlights data loader
├── requirements.txt        # Python dependencies
├── Dockerfile              # Application container
├── docker-compose.yml      # Multi-service orchestration
├── .env.example            # Environment configuration template
├── data/                   # OpenFlights datasets
├── templates/
│   └── index.html           # Main web interface
└── static/
    ├── css/style.css        # UI styling
    └── js/main.js            # Frontend logic + D3 visualization
```

---

## ⚡ Quick Start

### Option 1 — Docker Compose (recommended)

```bash
git clone https://github.com/Rana-fahar-26/Airline-Route-Graph-Explorer.git
cd Airline-Route-Graph-Explorer
docker compose up --build
```

Then open:

```text
http://localhost:5000
```

On first startup, the project downloads the OpenFlights datasets, loads MongoDB, and builds the Neo4j graph.

### Option 2 — Manual Setup

```bash
pip install -r requirements.txt
cp .env.example .env
python setup_db.py
python app.py
```

Make sure MongoDB and Neo4j are running and the values in `.env` match your local configuration.

---

## 🌐 REST API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/stats` | Graph-level statistics |
| `GET` | `/api/airports/search?q=` | Search airports |
| `GET` | `/api/airports/<IATA>` | Airport details |
| `GET` | `/api/routes/<IATA>` | Outbound routes |
| `GET` | `/api/shortest-path?from=&to=` | Shortest path analysis |
| `GET` | `/api/graph/sample` | Sample graph for visualization |
| `GET` | `/api/connectivity/<IATA>` | Degree and reachability metrics |

Example:

```bash
curl "http://localhost:5000/api/airports/search?q=dubai"
curl "http://localhost:5000/api/routes/DXB"
curl "http://localhost:5000/api/shortest-path?from=LHR&to=SIN&mode=hops"
```

---

## 📊 Dataset

AeroGraph uses the **OpenFlights** dataset containing airport, route, and airline information.

| Dataset | Approx. records | Description |
|---|---:|---|
| `airports.dat` | ~7,500 | Airport metadata and coordinates |
| `routes.dat` | ~67,000 | Airline route relationships |
| `airlines.dat` | ~5,888 | Airline names and codes |

Source: [OpenFlights Data](https://openflights.org/data.html)

---

## 🔐 Configuration

Copy the example environment file and configure your local database credentials:

```bash
cp .env.example .env
```

Typical settings include:

```env
MONGO_URI=...
NEO4J_URI=...
NEO4J_USER=...
NEO4J_PASS=...
```

> Never commit real credentials, API keys, or production secrets to GitHub.

---

## 🎓 What This Project Demonstrates

This project brings together several practical software-engineering and computer-science concepts:

- REST API development with Flask
- Graph data modeling with Neo4j
- Document data modeling with MongoDB
- BFS and shortest-path concepts
- Dijkstra-based weighted routing
- Data ingestion and transformation
- Interactive data visualization with D3.js
- Docker-based development environments
- Full-stack application architecture

---

## 👨‍💻 Author

**Fahar Inam Rana**  
Computer Science Student · AI Engineer · Full-Stack Developer

- GitHub: [@Rana-fahar-26](https://github.com/Rana-fahar-26)
- LinkedIn: [Fahar Inam Rana](https://www.linkedin.com/in/rana-fahar-inam-156034363/)
- Email: `ranafaharinam@gmail.com`

---

## 📌 Status

**Active portfolio project** — continuously improving the architecture, visualization, and developer experience.

---

⭐ If you find this project useful, consider giving it a star.