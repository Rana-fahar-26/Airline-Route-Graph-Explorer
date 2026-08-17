"""Download OpenFlights data and build MongoDB + Neo4j datasets."""

import csv
import logging
import math
import os
import sys
import urllib.request

from neo4j import GraphDatabase
from pymongo import ASCENDING, MongoClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "")
DB_NAME = "airline_routes"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

OPENFLIGHTS_URLS = {
    "airports": "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat",
    "routes": "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat",
    "airlines": "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat",
}


def haversine(lat1, lon1, lat2, lon2):
    """Return great-circle distance in kilometres."""
    radius = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def download_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    for name, url in OPENFLIGHTS_URLS.items():
        path = os.path.join(DATA_DIR, f"{name}.dat")
        if os.path.exists(path):
            log.info("%s.dat already present; skipping download", name)
            continue
        log.info("Downloading %s.dat", name)
        try:
            urllib.request.urlretrieve(url, path)
        except Exception as exc:
            log.error("Failed to download %s: %s", name, exc)
            sys.exit(1)


def load_mongo():
    log.info("Connecting to MongoDB")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    db.airports.drop()
    airports = []
    airport_index = {}
    with open(os.path.join(DATA_DIR, "airports.dat"), encoding="utf-8", errors="replace") as file:
        for row in csv.reader(file):
            if len(row) < 14:
                continue
            try:
                internal_id = row[0].strip()
                iata = row[4].strip().strip('"')
                icao = row[5].strip().strip('"')
                lat = float(row[6])
                lon = float(row[7])
            except (ValueError, IndexError):
                continue
            if not iata or iata == r"\N":
                continue
            airports.append({
                "internal_id": internal_id,
                "name": row[1].strip().strip('"'),
                "city": row[2].strip().strip('"'),
                "country": row[3].strip().strip('"'),
                "iata": iata,
                "icao": icao,
                "lat": lat,
                "lon": lon,
                "alt": row[8].strip(),
                "tz": row[9].strip(),
                "dst": row[10].strip(),
                "timezone": row[11].strip(),
                "type": row[12].strip(),
                "source": row[13].strip(),
            })
            airport_index[internal_id] = iata

    if airports:
        db.airports.insert_many(airports)
        db.airports.create_index([("iata", ASCENDING)], unique=True)
        db.airports.create_index([("city", ASCENDING)])
        db.airports.create_index([("country", ASCENDING)])
        db.airports.create_index([("name", ASCENDING)])
    log.info("Loaded %s airports", len(airports))

    coord_map = {airport["iata"]: (airport["lat"], airport["lon"]) for airport in airports}

    db.airlines.drop()
    airlines = []
    with open(os.path.join(DATA_DIR, "airlines.dat"), encoding="utf-8", errors="replace") as file:
        for row in csv.reader(file):
            if len(row) < 8:
                continue
            airlines.append({
                "internal_id": row[0].strip(),
                "name": row[1].strip().strip('"'),
                "alias": row[2].strip().strip('"'),
                "iata": row[3].strip().strip('"'),
                "icao": row[4].strip().strip('"'),
                "callsign": row[5].strip().strip('"'),
                "country": row[6].strip().strip('"'),
                "active": row[7].strip().strip('"') == "Y",
            })
    if airlines:
        db.airlines.insert_many(airlines)
    log.info("Loaded %s airlines", len(airlines))

    db.routes.drop()
    routes = []
    with open(os.path.join(DATA_DIR, "routes.dat"), encoding="utf-8", errors="replace") as file:
        for row in csv.reader(file):
            if len(row) < 9:
                continue
            src_iata, dst_iata = row[2].strip(), row[4].strip()
            if not src_iata or not dst_iata or src_iata == r"\N" or dst_iata == r"\N":
                continue
            distance = None
            if src_iata in coord_map and dst_iata in coord_map:
                source = coord_map[src_iata]
                destination = coord_map[dst_iata]
                distance = round(haversine(source[0], source[1], destination[0], destination[1]))
            routes.append({
                "airline": row[0].strip(),
                "airline_id": row[1].strip(),
                "src_iata": src_iata,
                "src_id": row[3].strip(),
                "dst_iata": dst_iata,
                "dst_id": row[5].strip(),
                "codeshare": row[6].strip() == "Y",
                "stops": int(row[7]) if row[7].strip().isdigit() else 0,
                "equipment": row[8].strip() if len(row) > 8 else "",
                "distance_km": distance,
            })
    if routes:
        db.routes.insert_many(routes)
        db.routes.create_index([("src_iata", ASCENDING)])
        db.routes.create_index([("dst_iata", ASCENDING)])
    log.info("Loaded %s routes", len(routes))

    client.close()
    return coord_map, routes


def load_neo4j(coord_map, routes):
    log.info("Connecting to Neo4j")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    mongo_client = MongoClient(MONGO_URI)

    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        airports = list(mongo_client[DB_NAME].airports.find({}, {"_id": 0}))
        batch_size = 500

        for start in range(0, len(airports), batch_size):
            session.run(
                """
                UNWIND $batch AS a
                MERGE (n:Airport {iata: a.iata})
                SET n.name=a.name, n.city=a.city, n.country=a.country,
                    n.lat=a.lat, n.lon=a.lon, n.icao=a.icao,
                    n.alt=a.alt, n.tz=a.tz
                """,
                batch=airports[start:start + batch_size],
            )

        route_params = [
            {
                "src": route["src_iata"],
                "dst": route["dst_iata"],
                "airline": route["airline"],
                "stops": route["stops"],
                "distance": route.get("distance_km") or 0,
                "equipment": route.get("equipment", ""),
            }
            for route in routes
            if route["src_iata"] and route["dst_iata"]
        ]
        for start in range(0, len(route_params), batch_size):
            session.run(
                """
                UNWIND $batch AS r
                MATCH (src:Airport {iata: r.src})
                MATCH (dst:Airport {iata: r.dst})
                MERGE (src)-[rel:ROUTE {airline: r.airline}]->(dst)
                SET rel.stops=r.stops, rel.distance=r.distance,
                    rel.equipment=r.equipment
                """,
                batch=route_params[start:start + batch_size],
            )
        session.run("CREATE INDEX airport_iata IF NOT EXISTS FOR (a:Airport) ON (a.iata)")

    mongo_client.close()
    driver.close()
    log.info("Neo4j graph build complete")


if __name__ == "__main__":
    log.info("Airline Route Graph Explorer — database setup")
    download_data()
    coordinates, route_data = load_mongo()
    load_neo4j(coordinates, route_data)
    log.info("Setup complete. Run: python app.py")
