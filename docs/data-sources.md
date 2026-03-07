# Data Sources & APIs

Research into available data sources for tracking celestial objects.

## Core Positional Data

### JPL Horizons API

The single most important source — provides real-time positional ephemeris (RA/Dec, altitude/azimuth, distance, magnitude, rise/set times) for all categories of solar system objects from any observer location.

- **Endpoint:** `https://ssd.jpl.nasa.gov/api/horizons.api`
- **Objects:** 1.4M+ asteroids, 4k+ comets, 424 natural satellites, all planets, Sun, 239 spacecraft
- **Auth:** None
- **Cost:** Free
- **Rate limits:** One concurrent request at a time (no parallel requests)
- **Format:** JSON or plain text
- **CORS:** Blocked — server-side/script access only
- **Docs:** https://ssd-api.jpl.nasa.gov/doc/horizons.html

**Ephemeris types:** OBSERVER (topocentric RA/Dec), VECTORS (Cartesian state), ELEMENTS (orbital), SPK (binary trajectory), APPROACH (close-approach tables)

**Key parameters:**
| Parameter | Description | Example |
|---|---|---|
| `COMMAND` | Target body | `'499'` (Mars), `'10'` (Sun), `'301'` (Moon) |
| `EPHEM_TYPE` | Output type | `'OBSERVER'`, `'VECTORS'`, `'ELEMENTS'` |
| `CENTER` | Observer location | `'500@399'` (geocentric Earth) |
| `START_TIME` / `STOP_TIME` | Date range | `'2026-01-01'` |
| `STEP_SIZE` | Interval | `'1 d'`, `'60 min'` |
| `QUANTITIES` | Data columns | Numeric codes selecting output fields |
| `TLIST` | Discrete times | Up to 10,000 time points |

**Example:**

```
https://ssd.jpl.nasa.gov/api/horizons.api?format=json&COMMAND='499'&EPHEM_TYPE='OBSERVER'&CENTER='500@399'&START_TIME='2026-03-01'&STOP_TIME='2026-03-08'&STEP_SIZE='1%20d'&QUANTITIES='1,9,20,23'
```

### Astronomy API (astronomyapi.com)

Simpler REST API for planet/Sun/Moon positions. No asteroids or comets.

- **Endpoint:** `https://api.astronomyapi.com/api/v2/`
- **Auth:** Basic Auth (free sign-up, get Application ID + Secret)
- **Rate limit:** ~3 requests/second
- **Objects:** Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune
- **Data:** Distance, altitude/azimuth, RA/Dec, constellation, magnitude, elongation, Moon phases
- **Constraint:** 366-day max date range per request
- **Docs:** https://docs.astronomyapi.com/

**Key endpoints:**

- `GET /bodies` — list available bodies
- `GET /bodies/positions?latitude=...&longitude=...&from_date=...&to_date=...&time=...` — positions
- `GET /search` — stars and deep-sky objects

### Local Ephemeris Libraries

Compute positions offline with no API dependency. Choice depends on language.

| Library                      | Languages                 | Accuracy                 | License          | Notes                               |
| ---------------------------- | ------------------------- | ------------------------ | ---------------- | ----------------------------------- |
| **Astronomy Engine**         | C, C#, Python, JS, Kotlin | ~1 arcmin                | MIT              | Zero dependencies, multi-language   |
| **Skyfield**                 | Python                    | ~0.0005 arcsec           | MIT              | Uses JPL DE440, high precision      |
| **Swiss Ephemeris**          | C (+ many bindings)       | Professional-grade       | GPL / commercial | De facto standard for precision     |
| **astro**                    | Rust                      | Meeus algorithms         | —                | Planetary/solar/lunar positions     |
| **swisseph**                 | Rust (wrapper)            | Professional-grade       | —                | Rust wrapper for Swiss Ephemeris    |
| **practical-astronomy-rust** | Rust                      | Duffett-Smith algorithms | —                | —                                   |
| **soniakeys/meeus**          | Go                        | Meeus algorithms         | —                | Full Meeus implementation           |
| **mshafiee/jpl**             | Go                        | NASA-standard            | —                | Reads JPL DE binary files           |
| **mshafiee/swephgo**         | Go                        | Professional-grade       | —                | Go bindings for Swiss Ephemeris     |
| **libnova**                  | C/C++                     | VSOP87/ELP82             | LGPL             | General-purpose celestial mechanics |

**JPL DE440 ephemeris files** can also be used directly (~128 MB download from https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440.bsp) via SPICE toolkit or compatible libraries.

## Asteroid & Comet Data

### JPL Small-Body Database (SBDB) APIs

Suite of APIs from JPL Solar System Dynamics. All free, no auth, one-concurrent-request limit.

**SBDB Lookup** — detailed data for a single object (orbital elements, physical params, close approaches, discovery info):

- `GET https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=Eros&phys-par=1&ca-data=1`
- Docs: https://ssd-api.jpl.nasa.gov/doc/sbdb.html

**SBDB Query** — filtered queries across all small bodies:

- `GET https://ssd-api.jpl.nasa.gov/sbdb_query.api?fields=full_name,epoch,e,a,q,i,om,w&sb-class=IEO`
- Docs: https://ssd-api.jpl.nasa.gov/doc/sbdb_query.html

**Close-Approach Data** — upcoming/past close approaches to Earth (or other bodies):

- `GET https://ssd-api.jpl.nasa.gov/cad.api?date-min=2026-01-01&dist-max=0.2`
- Defaults: next 60 days, within 0.05 AU
- Docs: https://ssd-api.jpl.nasa.gov/doc/cad.html

**Sentry** — impact risk monitoring (Palermo/Torino scale, impact probability):

- `GET https://ssd-api.jpl.nasa.gov/sentry.api?des=99942` (Apophis)
- Docs: https://ssd-api.jpl.nasa.gov/doc/sentry.html

**Scout** — real-time hazard assessment for newly discovered NEO candidates:

- `GET https://ssd-api.jpl.nasa.gov/scout.api`

**Fireball** — atmospheric fireball/bolide events (date, location, energy, velocity):

- `GET https://ssd-api.jpl.nasa.gov/fireball.api?date-min=2024-01-01&limit=20`
- Docs: https://ssd-api.jpl.nasa.gov/doc/fireball.html

**Small-Body Identification** — find known small bodies within a field of view at a specific time:

- `GET https://ssd-api.jpl.nasa.gov/sb_ident.api`

**Small-Body Observability** — list observable small bodies from a location on a date:

- `GET https://ssd-api.jpl.nasa.gov/sbwobs.api`

**JD Date/Time Converter** — Julian date <-> calendar date:

- `GET https://ssd-api.jpl.nasa.gov/jd_cal.api`

### NASA NeoWs (Near Earth Object Web Service)

Near-Earth asteroid data via api.nasa.gov.

- **Auth:** Free API key from https://api.nasa.gov (`DEMO_KEY` available for testing)
- **Rate limits:** 1,000 req/hr (registered key), 30 req/hr (DEMO_KEY)

**Endpoints:**

- **Feed:** `GET https://api.nasa.gov/neo/rest/v1/feed?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&api_key=KEY` (max 7-day span)
- **Lookup:** `GET https://api.nasa.gov/neo/rest/v1/neo/{asteroid_id}?api_key=KEY`
- **Browse:** `GET https://api.nasa.gov/neo/rest/v1/neo/browse?api_key=KEY`

### Minor Planet Center (IAU/MPC)

Official clearinghouse for asteroid and comet observations and orbits. 1.3M+ minor planets.

- **Bulk download:** MPCORB.DAT at https://www.minorplanetcenter.net/iau/MPCORB.html
- **Python:** `astroquery.mpc`
- **Web search:** https://www.minorplanetcenter.net/db_search

### Asterank API

Simple REST wrapper over MPC data for 600k+ asteroids.

- `GET https://www.asterank.com/api/mpc?query={"e":{"$lt":"0.5"}}&limit=10`
- Free, no auth

## Star Catalogs

| Catalog       | Coverage                                                                                  | Access                                                                                       |
| ------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **Gaia DR3**  | ~1.8 billion stars — positions, parallaxes, proper motions, radial velocities, photometry | Free TAP queries: `https://gea.esac.esa.int/tap-server/tap`                                  |
| **Hipparcos** | ~118,000 bright stars, high-precision astrometry                                          | VizieR (catalog I/239), bulk download from ESA                                               |
| **Tycho-2**   | ~2.5 million stars, positions and proper motions                                          | VizieR, bulk download from ESA                                                               |
| **SIMBAD**    | 16M objects — identifications, coordinates, classifications, bibliography                 | Free REST: `https://simbad.cds.unistra.fr/simbad/sim-id?Ident=Betelgeuse&output.format=JSON` |
| **VizieR**    | Thousands of catalogs (unified access)                                                    | `https://vizier.cds.unistra.fr/` — TAP, URL queries, `astroquery.vizier`                     |

**Gaia DR3 example query:**

```
https://gea.esac.esa.int/tap-server/tap/sync?REQUEST=doQuery&LANG=ADQL&FORMAT=json&QUERY=SELECT+TOP+10+source_id,ra,dec,parallax,phot_g_mean_mag+FROM+gaiadr3.gaia_source+WHERE+parallax>50
```

## Satellite Tracking

| Source              | Auth         | Format           | Notes                                                                                                                                                                             |
| ------------------- | ------------ | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CelesTrak**       | None         | TLE/JSON/XML/CSV | Standard community source. `https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=JSON` (ISS). Cache locally; re-fetch only every 2hrs. Will ban for excessive requests. |
| **TLE API**         | None         | JSON             | Simpler alternative: `https://tle.ivanstanojevic.me/api/tle/25544`                                                                                                                |
| **Space-Track.org** | Free account | Various          | Official US gov upstream source for satellite data                                                                                                                                |

## Solar / Space Weather

### NASA DONKI (api.nasa.gov)

Space weather events — solar flares, CMEs, geomagnetic storms, solar energetic particles.

- **Base:** `https://api.nasa.gov/DONKI/`
- **Auth:** Same api.nasa.gov key as NeoWs
- **Endpoints:** `CME`, `FLR`, `SEP`, `GST`, `IPS`, `MPC`, `HSS` (append to base with date params)
- **Docs:** https://ccmc.gsfc.nasa.gov/tools/DONKI/

## Other NASA APIs (api.nasa.gov)

- **APOD** (Astronomy Picture of the Day): `GET https://api.nasa.gov/planetary/apod?api_key=KEY&date=YYYY-MM-DD`
- **EPIC** (Earth imaging from DSCOVR): `GET https://api.nasa.gov/EPIC/api/natural/date/YYYY-MM-DD?api_key=KEY` — includes Sun/Earth positional metadata

## Recommended Architecture

**Tier 1 — Start here:**

1. **Local ephemeris library** for planets/Sun/Moon — works offline for the most common use case
2. **JPL Horizons API** for real-time positional data when local computation isn't sufficient
3. **JPL Close Approach API** for upcoming asteroid flybys

**Tier 2 — Add later:** 4. **NeoWs** for near-Earth asteroid alerts 5. **CelesTrak** for satellite tracking (ISS, Hubble, etc.) 6. **Sentry/Fireball APIs** for impact risk and fireball events 7. **SIMBAD** or a local star catalog for star identification
