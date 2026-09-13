# Demo Script

1. **Problem framing (30s)** — show a raw FIRMS map: undifferentiated red
   dots, no way to tell a refinery flare from a wildfire.
2. **Data fusion (1 min)** — show the same region with OSM industrial
   polygons + land cover overlaid, explain the four signal types
   (location, temporal pattern, intensity, seasonality).
3. **Classification output (1 min)** — switch to the live map, filter by
   class, show a known flare correctly tagged `persistent_industrial`
   and a Punjab cluster correctly tagged `agricultural_burning`.
4. **The money shot (1 min)** — show an `industrial_fire` (anomaly) alert:
   same facility as a `persistent_industrial` point, but FRP spiking
   3-6x its own historical baseline. Explain why relative deviation,
   not raw FRP, is the signal.
5. **Architecture (30s)** — one slide: FIRMS/OSM/land cover → features →
   XGBoost → PostGIS → FastAPI → map.
6. **Limitations, stated up front (30s)** — satellite revisit gaps
   (3-4h FIRMS latency), 4km INSAT resolution trade-off, weak-label
   noise. Framing this honestly reads as maturity, not weakness.
