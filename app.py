"""
Airline Route Graph Explorer - Flask Backend
Connects MongoDB (raw data) and Neo4j (graph processing)
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from pymongo import MongoClient
from neo4j import GraphDatabase
import os
import logging

# ─── Logging ───────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── App Setup ─────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ─── Configuration (FIXED) ─────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

# FIXED: Neo4j connection (IMPORTANT)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "asDF3487")

DB_NAME = "airline_routes"

# ─── Database Connections ───────────────────────────────────────────────
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[DB_NAME]

neo4j_driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASS)
)

# ─── Routes ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/stats")
def get_stats():
    try:
        airport_count = mongo_db.airports.count_documents({})
        route_count = mongo_db.routes.count_documents({})
        airline_count = mongo_db.airlines.count_documents({})

        with neo4j_driver.session(database="neo4j") as session:
            node_count = session.run(
                "MATCH (a:Airport) RETURN count(a) AS cnt"
            ).single()["cnt"]

            edge_count = session.run(
                "MATCH ()-[r:ROUTE]->() RETURN count(r) AS cnt"
            ).single()["cnt"]

        return jsonify({
            "airports": airport_count,
            "routes": route_count,
            "airlines": airline_count,
            "graph_nodes": node_count,
            "graph_edges": edge_count
        })

    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/airports/search")
def search_airports():
    query = request.args.get("q", "").strip()
    limit = int(request.args.get("limit", 10))

    if not query or len(query) < 2:
        return jsonify([])

    try:
        regex = {"$regex": query, "$options": "i"}

        results = mongo_db.airports.find(
            {"$or": [
                {"name": regex},
                {"city": regex},
                {"country": regex},
                {"iata": regex},
                {"icao": regex}
            ]},
            {"_id": 0}
        ).limit(limit)

        return jsonify(list(results))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/airports/<iata>")
def get_airport(iata):
    try:
        airport = mongo_db.airports.find_one(
            {"iata": iata.upper()},
            {"_id": 0}
        )

        if not airport:
            return jsonify({"error": "Airport not found"}), 404

        return jsonify(airport)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/routes/<iata>")
def get_routes(iata):
    try:
        with neo4j_driver.session(database="neo4j") as session:
            result = session.run("""
                MATCH (src:Airport {iata: $iata})-[r:ROUTE]->(dst:Airport)
                RETURN dst.iata AS destination,
                       dst.name AS dest_name,
                       dst.city AS dest_city,
                       dst.country AS dest_country,
                       dst.lat AS dest_lat,
                       dst.lon AS dest_lon,
                       r.airline AS airline,
                       r.stops AS stops
                LIMIT 100
            """, iata=iata.upper())

            routes = [dict(record) for record in result]

        src = mongo_db.airports.find_one(
            {"iata": iata.upper()},
            {"_id": 0}
        )

        return jsonify({
            "source": src,
            "routes": routes,
            "count": len(routes)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/shortest-path")
def shortest_path():
    src = request.args.get("from", "").upper()
    dst = request.args.get("to", "").upper()
    mode = request.args.get("mode", "hops")

    if not src or not dst:
        return jsonify({"error": "Both 'from' and 'to' required"}), 400

    try:
        with neo4j_driver.session(database="neo4j") as session:

            if mode == "distance":
                cypher = """
                MATCH (src:Airport {iata:$src}), (dst:Airport {iata:$dst})
                CALL apoc.algo.dijkstra(src, dst, 'ROUTE>', 'distance')
                YIELD path, weight
                RETURN [n IN nodes(path) | {
                    iata: n.iata,
                    name: n.name,
                    city: n.city,
                    country: n.country,
                    lat: n.lat,
                    lon: n.lon
                }] AS stops,
                weight AS total_distance,
                length(path) AS hops
                """
            else:
                cypher = """
                MATCH (src:Airport {iata:$src}), (dst:Airport {iata:$dst}),
                path = shortestPath((src)-[:ROUTE*..15]->(dst))
                RETURN [n IN nodes(path) | {
                    iata: n.iata,
                    name: n.name,
                    city: n.city,
                    country: n.country,
                    lat: n.lat,
                    lon: n.lon
                }] AS stops,
                length(path) AS hops
                """

            record = session.run(cypher, src=src, dst=dst).single()

            if not record:
                return jsonify({
                    "found": False,
                    "message": "No path found"
                })

            stops = record["stops"]

            result = {
                "found": True,
                "from": src,
                "to": dst,
                "hops": record["hops"],
                "stops": stops,
                "edges": []
            }

            for i in range(len(stops) - 1):
                result["edges"].append({
                    "from": stops[i]["iata"],
                    "to": stops[i + 1]["iata"]
                })

            if mode == "distance" and "total_distance" in record:
                result["total_distance_km"] = round(record["total_distance"])

            return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/connectivity/<iata>")
def connectivity(iata):
    try:
        with neo4j_driver.session(database="neo4j") as session:

            result = session.run("""
                MATCH (a:Airport {iata:$iata})
                OPTIONAL MATCH (a)-[:ROUTE]->(out:Airport)
                OPTIONAL MATCH (in:Airport)-[:ROUTE]->(a)
                RETURN count(DISTINCT out) AS out_degree,
                       count(DISTINCT in) AS in_degree,
                       count(DISTINCT out) + count(DISTINCT in) AS total_degree
            """, iata=iata.upper()).single()

            reach = session.run("""
                MATCH (src:Airport {iata:$iata})-[:ROUTE*1..2]->(dst:Airport)
                WHERE dst.iata <> $iata
                RETURN count(DISTINCT dst) AS reachable
            """, iata=iata.upper()).single()

            return jsonify({
                "iata": iata.upper(),
                "out_degree": result["out_degree"],
                "in_degree": result["in_degree"],
                "total_degree": result["total_degree"],
                "reachable_2hops": reach["reachable"]
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Run Server ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Server starting...")
    app.run(debug=True, host="127.0.0.1", port=5000)