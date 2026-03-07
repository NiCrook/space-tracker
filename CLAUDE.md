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

## Reference Docs

- `docs/data-sources.md` — full API and data source reference
- `docs/horizons-api-notes.md` — Horizons response format, parsing notes, gotchas, COMMAND/QUANTITIES codes
- `docs/roadmap.md` — phased feature plan
