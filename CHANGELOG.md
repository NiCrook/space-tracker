# Changelog

## [1.1.0] - 2026-03-10

### Features

- (sky-now) expand tracked objects with progressive loading and dim below-horizon styling

### Refactoring

- (sky-now) remove automatic 5-minute refresh interval

### Other

- add CODEOWNERS for required code owner reviews

## [1.0.0] - 2026-03-09

### Features

- scaffold project with Textual TUI and Horizons API client
- (config) add location setup screen with IP geolocation auto-detect
- (sky-now) wire up live celestial object data loading
- (object-detail) add drill-down view with rise/set/transit times
- (api) add ephemeris cache and fix column parser for solar marker
- (close-approaches) wire up Close Approaches tab with JPL CAD API
- (search) wire up Search tab with Horizons lookup
- (solar-activity) add Solar Activity tab with NASA DONKI API
- (events) add Events Calendar tab with conjunctions, oppositions, showers, eclipses

### Documentation

- (roadmap) mark phases 1-2 as completed
- add README with features, install instructions, and screenshot

### Other

- Initial commit: project docs and research
