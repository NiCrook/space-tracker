# JPL Horizons API Notes

## Response Format

The API returns JSON with a single `result` field containing a large text blob. The actual ephemeris data is not structured JSON — it must be parsed from the text.

### Data Location

Ephemeris rows are between `$$SOE` (Start of Ephemeris) and `$$EOE` (End of Ephemeris) markers:

```
$$SOE
 2026-Mar-07 00:00     22 21 48.06 -11 23 00.4        n.a.       n.a.    1.136   3.884  2.33265492552914  -2.5064899   12.9930 /L
 2026-Mar-08 00:00     22 24 47.61 -11 05 49.6        n.a.       n.a.    1.158   3.907  2.33120549156146  -2.5128926   13.2048 /L
$$EOE
```

### Column Format

- Fixed-width, space-delimited
- Columns depend on which `QUANTITIES` are requested
- Column headers appear just above `$$SOE` in the text blob
- RA is in HMS format: `HH MM SS.ff`
- Dec is in DMS format: `sDD MN SC.f`
- Values may be `n.a.` when not applicable

## Gotchas

### Azimuth/Elevation requires topocentric location

Geocentric queries (`CENTER='500@399'`) return `n.a.` for azimuth and elevation. To get alt/az (needed for Sky Now), you must specify a topocentric observer location:

```
CENTER='coord@399'
COORD_TYPE='GEODETIC'
SITE_COORD='<longitude>,<latitude>,<elevation_km>'
```

Longitude is East-positive. Elevation is in km.

### One concurrent request limit

The API allows only one request at a time. Requests must be serialized, not parallelized. Batch by requesting multiple time steps in a single call rather than making many calls.

### Useful QUANTITIES codes

| Code | Field                                 |
| ---- | ------------------------------------- |
| 1    | Astrometric RA & DEC (ICRF)           |
| 4    | Apparent AZ & EL                      |
| 9    | Visual magnitude & surface brightness |
| 20   | Range (delta) & range-rate (deldot)   |
| 23   | Solar elongation angle                |
| 31   | Observer ecliptic lon & lat           |
| 42   | Observer sub-longitude & sub-latitude |

Full list: https://ssd-api.jpl.nasa.gov/doc/horizons.html

### Common COMMAND values

| Body    | COMMAND |
| ------- | ------- |
| Sun     | `'10'`  |
| Moon    | `'301'` |
| Mercury | `'199'` |
| Venus   | `'299'` |
| Mars    | `'499'` |
| Jupiter | `'599'` |
| Saturn  | `'699'` |
| Uranus  | `'799'` |
| Neptune | `'899'` |

Asteroids and comets can be queried by name or designation (e.g., `'Ceres'`, `'433'` for Eros).

## Sample Request

```
https://ssd.jpl.nasa.gov/api/horizons.api?format=json&COMMAND='499'&EPHEM_TYPE='OBSERVER'&CENTER='coord@399'&COORD_TYPE='GEODETIC'&SITE_COORD='-122.4194,37.7749,0.01'&START_TIME='2026-03-07'&STOP_TIME='2026-03-08'&STEP_SIZE='60 min'&QUANTITIES='1,4,9,20,23'
```
