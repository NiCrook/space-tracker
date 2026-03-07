# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Space Tracker is a terminal user interface (TUI) application for amateur astronomers to track space objects including planets, the Sun, moons, asteroids, and other celestial bodies.

## Tech Stack

- **Language:** Python
- **TUI Framework:** Textual (by Textualize) — CSS-like styling/layout, native asyncio, rich widget set
- **HTTP Client:** httpx — async-native, clean API
- **Testing:** pytest
- **Package Manager:** uv
- **Python Version:** 3.12+
- **Primary Data Source:** JPL Horizons API (`https://ssd.jpl.nasa.gov/api/horizons.api`) — free, no auth, covers all solar system objects. Response is a text blob in JSON that must be parsed (see docs).

## Commands

```bash
uv sync --dev          # Install all dependencies
uv run space-tracker   # Run the app
uv run pytest -v       # Run all tests
uv run pytest tests/test_horizons_parser.py::test_parse_ephemeris_first_row  # Run a single test
```

## Architecture

```
space_tracker/
  app.py              # Textual App — main entry point, tab layout, keybindings
  config.py           # User config (location) — persisted to ~/.config/space-tracker/
  api/
    horizons.py       # JPL Horizons client + response parser ($$SOE/$$EOE text parsing)
  tabs/
    sky_now.py        # "Sky Now" tab — visible objects from user's location
    object_detail.py  # "Object Detail" tab — drill-down view for a selected object
    close_approaches.py  # "Close Approaches" tab — upcoming asteroid flybys
    search.py         # "Search" tab — look up any object by name/designation
```

The app follows Textual's composition pattern: `SpaceTrackerApp` composes `TabbedContent` with tab panes, each containing a tab widget from `tabs/`. API calls are async via httpx, fitting naturally into Textual's asyncio event loop.

## Reference Docs

- `docs/data-sources.md` — full API and data source reference
- `docs/horizons-api-notes.md` — Horizons response format, parsing notes, gotchas, COMMAND/QUANTITIES codes
- `docs/roadmap.md` — phased feature plan
