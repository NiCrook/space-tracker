# Roadmap

## Phase 1: Foundation

- Project scaffolding (Textual app, project structure, dependencies)
- Location configuration (lat/lon/elevation via config file or first-run prompt)
- JPL Horizons API client (async, with caching and request batching)
- **Sky Now tab** — objects currently visible from the user's location (planets, Sun, Moon) with altitude/azimuth, magnitude
- **Object Detail tab** — drill into a selected object for rise/set times, distance, RA/Dec, elongation

## Phase 2: Asteroids & Search

- **Close Approaches tab** — upcoming asteroid flybys from JPL Close Approach API (size, distance, velocity, date)
- **Search tab** — look up any object by name/designation via Horizons, display position and details

## Phase 3: Solar & Events

- ~~**Solar Activity tab** — solar flares, CMEs, geomagnetic storms from NASA DONKI API~~ **Done**
- ~~**Events Calendar tab** — conjunctions, oppositions, meteor showers, eclipses~~ **Done**

## Phase 4: Extended Objects

- **Satellites tab** — ISS, Hubble, etc. via CelesTrak TLE data
- **Stars/Deep-Sky tab** — star and deep-sky object lookup via SIMBAD or Gaia
- Constellation column in Sky Now (derive from RA/Dec using IAU boundary data)
