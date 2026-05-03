"""
setup_db.py
───────────
Downloads the OpenFlights dataset, loads it into MongoDB,
then builds a Neo4j graph (Airport nodes + ROUTE relationships).

Run once before starting the Flask app:
    python setup_db.py
"""

import csv
import os
import sys
import math
import logging
import urllib.request
from pymongo import MongoClient, ASCENDING
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────
MONGO_URI  = os.getenv("MONGO_URI",  "mongodb://localhost:27017/")
NEO4J_URI  = os.getenv("NEO4J_URI",  "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "asDF3487")
DB_NAME    = "airline_routes"
DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")

OPENFLIGHTS_URLS = {
    "airports": "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat",
    "routes":   "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat",
    "airlines": "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat",
}

# ─── Helpers ─────────────────────────────────────────────────────────────────

def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in km."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def download_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    for name, url in OPENFLIGHTS_URLS.items():
        path = os.path.join(DATA_DIR, f"{name}.dat")
        if os.path.exists(path):
            log.info(f"  {name}.dat already present, skipping download")
            continue
        log.info(f"  Downloading {name}.dat …")
        try:
            urllib.request.urlretrieve(url, path)
            log.info(f"  ✓ {name}.dat saved")
        except Exception as e:
            log.error(f"  ✗ Failed to download {name}: {e}")
            sys.exit(1)


# ─── MongoDB ──────────────────────────────────────────────────────────────────

def load_mongo():
    log.info("Connecting to MongoDB …")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # ── Airports ──────────────────────────────────────────────────────────────
    log.info("Loading airports into MongoDB …")
    db.airports.drop()
    airports = []
    airport_index = {}   # internal_id → iata for route resolution

    with open(os.path.join(DATA_DIR, "airports.dat"), encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) < 14:
                continue
            try:
                internal_id = row[0].strip()
                iata = row[4].strip().strip('"')
                icao = row[5].strip().strip('"')
                lat  = float(row[6])
                lon  = float(row[7])
            except (ValueError, IndexError):
                continue

            if not iata or iata == r"\N":
                continue

            doc = {
                "internal_id": internal_id,
                "name":    row[1].strip().strip('"'),
                "city":    row[2].strip().strip('"'),
                "country": row[3].strip().strip('"'),
                "iata":    iata,
                "icao":    icao,
                "lat":     lat,
                "lon":     lon,
                "alt":     row[8].strip(),
                "tz":      row[9].strip(),
                "dst":     row[10].strip(),
                "timezone": row[11].strip(),
                "type":    row[12].strip() if len(row) > 12 else "",
                "source":  row[13].strip() if len(row) > 13 else "",
            }
            airports.append(doc)
            airport_index[internal_id] = iata

    if airports:
        db.airports.insert_many(airports)
        db.airports.create_index([("iata", ASCENDING)], unique=True)
        db.airports.create_index([("city", ASCENDING)])
        db.airports.create_index([("country", ASCENDING)])
        db.airports.create_index([("name", ASCENDING)])
    log.info(f"  ✓ {len(airports)} airports loaded")

    # Build lat/lon lookup
    coord_map = {a["iata"]: (a["lat"], a["lon"]) for a in airports}

    # ── Airlines ──────────────────────────────────────────────────────────────
    log.info("Loading airlines into MongoDB …")
    db.airlines.drop()
    airlines = []
    with open(os.path.join(DATA_DIR, "airlines.dat"), encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) < 8:
                continue
            iata_code = row[3].strip().strip('"')
            airlines.append({
                "internal_id": row[0].strip(),
                "name":    row[1].strip().strip('"'),
                "alias":   row[2].strip().strip('"'),
                "iata":    iata_code,
                "icao":    row[4].strip().strip('"'),
                "callsign": row[5].strip().strip('"'),
                "country": row[6].strip().strip('"'),
                "active":  row[7].strip().strip('"') == "Y",
            })
    if airlines:
        db.airlines.insert_many(airlines)
    log.info(f"  ✓ {len(airlines)} airlines loaded")

    # ── Routes ────────────────────────────────────────────────────────────────
    log.info("Loading routes into MongoDB …")
    db.routes.drop()
    routes = []
    with open(os.path.join(DATA_DIR, "routes.dat"), encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) < 9:
                continue
            src_iata = row[2].strip()
            dst_iata = row[4].strip()
            if not src_iata or not dst_iata or src_iata == r"\N" or dst_iata == r"\N":
                continue

            # Compute distance if coords available
            dist = None
            if src_iata in coord_map and dst_iata in coord_map:
                s, d = coord_map[src_iata], coord_map[dst_iata]
                dist = round(haversine(s[0], s[1], d[0], d[1]))

            routes.append({
                "airline":    row[0].strip(),
                "airline_id": row[1].strip(),
                "src_iata":   src_iata,
                "src_id":     row[3].strip(),
                "dst_iata":   dst_iata,
                "dst_id":     row[5].strip(),
                "codeshare":  row[6].strip() == "Y",
                "stops":      int(row[7]) if row[7].strip().isdigit() else 0,
                "equipment":  row[8].strip() if len(row) > 8 else "",
                "distance_km": dist,
            })
    if routes:
        db.routes.insert_many(routes)
        db.routes.create_index([("src_iata", ASCENDING)])
        db.routes.create_index([("dst_iata", ASCENDING)])
    log.info(f"  ✓ {len(routes)} routes loaded")

    client.close()
    return coord_map, routes


# ─── Neo4j ───────────────────────────────────────────────────────────────────

def load_neo4j(coord_map, routes):
    log.info("Connecting to Neo4j …")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

    with driver.session() as session:
        log.info("Clearing existing graph …")
        session.run("MATCH (n) DETACH DELETE n")

        log.info("Creating Airport nodes …")
        mongo_client = MongoClient(MONGO_URI)
        airports_col = mongo_client[DB_NAME].airports

        airports = list(airports_col.find({}, {"_id": 0}))
        batch_size = 500
        for i in range(0, len(airports), batch_size):
            batch = airports[i:i+batch_size]
            session.run("""
                UNWIND $batch AS a
                MERGE (n:Airport {iata: a.iata})
                SET n.name    = a.name,
                    n.city    = a.city,
                    n.country = a.country,
                    n.lat     = a.lat,
                    n.lon     = a.lon,
                    n.icao    = a.icao,
                    n.alt     = a.alt,
                    n.tz      = a.tz
            """, batch=batch)
        log.info(f"  ✓ {len(airports)} Airport nodes created")

        log.info("Creating ROUTE relationships …")
        route_params = [
            {
                "src": r["src_iata"],
                "dst": r["dst_iata"],
                "airline": r["airline"],
                "stops": r["stops"],
                "distance": r.get("distance_km") or 0,
                "equipment": r.get("equipment", ""),
            }
            for r in routes
            if r["src_iata"] and r["dst_iata"]
        ]

        for i in range(0, len(route_params), batch_size):
            batch = route_params[i:i+batch_size]
            session.run("""
                UNWIND $batch AS r
                MATCH (src:Airport {iata: r.src})
                MATCH (dst:Airport {iata: r.dst})
                MERGE (src)-[rel:ROUTE {airline: r.airline}]->(dst)
                SET rel.stops     = r.stops,
                    rel.distance  = r.distance,
                    rel.equipment = r.equipment
            """, batch=batch)
        log.info(f"  ✓ {len(route_params)} ROUTE relationships created")

        # Index
        try:
            session.run("CREATE INDEX airport_iata IF NOT EXISTS FOR (a:Airport) ON (a.iata)")
        except Exception:
            session.run("CREATE INDEX ON :Airport(iata)")

    driver.close()
    mongo_client.close()
    log.info("Neo4j graph build complete ✓")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("=" * 55)
    log.info("  Airline Route Graph Explorer — Database Setup")
    log.info("=" * 55)

    log.info("\n[1/3] Downloading OpenFlights dataset …")
    download_data()

    log.info("\n[2/3] Loading data into MongoDB …")
    coord_map, routes = load_mongo()

    log.info("\n[3/3] Building Neo4j graph …")
    load_neo4j(coord_map, routes)

    log.info("\n✅  Setup complete! Run:  python app.py")
