// ═══════════════════════════════════════════════════════════════
//  AeroGraph — Neo4j Cypher Query Reference
//  Run these in the Neo4j Browser at http://localhost:7474
// ═══════════════════════════════════════════════════════════════

// ── 1. View a sample of airports ─────────────────────────────
MATCH (a:Airport)
RETURN a.iata, a.name, a.city, a.country
LIMIT 20;

// ── 2. Count all nodes and edges ─────────────────────────────
MATCH (a:Airport) WITH count(a) AS nodes
MATCH ()-[r:ROUTE]->() WITH nodes, count(r) AS edges
RETURN nodes, edges;

// ── 3. Routes from London Heathrow ───────────────────────────
MATCH (src:Airport {iata: "LHR"})-[r:ROUTE]->(dst:Airport)
RETURN dst.iata, dst.name, dst.city, r.airline
ORDER BY dst.country;

// ── 4. Shortest path by hops: LHR → SIN ─────────────────────
MATCH (src:Airport {iata: "LHR"}), (dst:Airport {iata: "SIN"}),
      path = shortestPath((src)-[:ROUTE*..10]->(dst))
RETURN [n IN nodes(path) | n.iata] AS route,
       length(path) AS hops;

// ── 5. All paths up to 3 hops: JFK → DXB ────────────────────
MATCH (src:Airport {iata: "JFK"}), (dst:Airport {iata: "DXB"}),
      path = (src)-[:ROUTE*1..3]->(dst)
RETURN [n IN nodes(path) | n.iata] AS route,
       length(path) AS hops
ORDER BY hops
LIMIT 10;

// ── 6. Top 10 most connected airports (out-degree) ───────────
MATCH (a:Airport)-[:ROUTE]->()
RETURN a.iata, a.name, count(*) AS out_routes
ORDER BY out_routes DESC
LIMIT 10;

// ── 7. Top 10 airports by total degree ───────────────────────
MATCH (a:Airport)
OPTIONAL MATCH (a)-[:ROUTE]->(out)
OPTIONAL MATCH (in_a)-[:ROUTE]->(a)
WITH a,
     count(DISTINCT out)  AS out_degree,
     count(DISTINCT in_a) AS in_degree
RETURN a.iata, a.name,
       out_degree, in_degree,
       out_degree + in_degree AS total_degree
ORDER BY total_degree DESC
LIMIT 10;

// ── 8. Airports reachable from SIN in 2 hops ─────────────────
MATCH (src:Airport {iata: "SIN"})-[:ROUTE*1..2]->(dst:Airport)
WHERE dst.iata <> "SIN"
RETURN DISTINCT dst.iata, dst.name, dst.country
ORDER BY dst.country;

// ── 9. Route network between major hubs ──────────────────────
MATCH (a:Airport)-[r:ROUTE]->(b:Airport)
WHERE a.iata IN ["LHR","JFK","DXB","SIN","CDG","FRA","HKG","LAX"]
  AND b.iata IN ["LHR","JFK","DXB","SIN","CDG","FRA","HKG","LAX"]
RETURN a.iata AS from, b.iata AS to, r.airline AS airline;

// ── 10. Dijkstra shortest path by distance (needs APOC) ──────
MATCH (src:Airport {iata: "LHR"}), (dst:Airport {iata: "SYD"})
CALL apoc.algo.dijkstra(src, dst, "ROUTE>", "distance") YIELD path, weight
RETURN [n IN nodes(path) | n.iata] AS route,
       round(weight) AS distance_km;

// ── 11. Airports with no inbound routes ──────────────────────
MATCH (a:Airport)
WHERE NOT ()-[:ROUTE]->(a)
RETURN a.iata, a.name, a.country
LIMIT 20;

// ── 12. Airlines with most routes ────────────────────────────
MATCH ()-[r:ROUTE]->()
RETURN r.airline AS airline, count(*) AS route_count
ORDER BY route_count DESC
LIMIT 15;
