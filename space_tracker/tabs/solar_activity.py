from datetime import datetime, timedelta, timezone

import httpx
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import DataTable, Static
from textual.worker import Worker, WorkerState

from space_tracker.api.donki import (
    CoronalMassEjection,
    GeomagneticStorm,
    SolarFlare,
    fetch_cmes,
    fetch_geomagnetic_storms,
    fetch_solar_flares,
)


def kp_to_storm_level(kp: float) -> str:
    if kp >= 9:
        return "G5 (Extreme)"
    elif kp >= 8:
        return "G4 (Severe)"
    elif kp >= 7:
        return "G3 (Strong)"
    elif kp >= 6:
        return "G2 (Moderate)"
    elif kp >= 5:
        return "G1 (Minor)"
    else:
        return "Below Storm"


def format_flare_row(flare: SolarFlare) -> tuple[str, ...]:
    return (
        flare.class_type,
        flare.peak_time or "---",
        flare.begin_time,
        flare.end_time or "---",
        flare.source_location or "---",
        str(flare.active_region_num) if flare.active_region_num is not None else "---",
    )


def format_storm_row(storm: GeomagneticStorm) -> tuple[str, ...]:
    return (
        storm.start_time,
        f"{storm.kp_index_max:.1f}",
        kp_to_storm_level(storm.kp_index_max),
    )


def format_cme_row(cme: CoronalMassEjection) -> tuple[str, ...]:
    return (
        cme.start_time,
        f"{cme.speed:.0f}" if cme.speed is not None else "---",
        cme.cme_type or "---",
        f"{cme.half_angle:.0f}" if cme.half_angle is not None else "---",
        cme.source_location or "---",
        str(cme.active_region_num) if cme.active_region_num is not None else "---",
    )


class SolarActivityTab(Container):
    """Recent solar activity: flares, geomagnetic storms, and CMEs."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("Solar Activity — Space Weather Events", classes="tab-header")
        yield Static("", id="solar-status")
        yield Static("Solar Flares (past 7 days)", classes="tab-header")
        yield DataTable(id="flare-table")
        yield Static("Geomagnetic Storms (past 30 days)", classes="tab-header")
        yield DataTable(id="storm-table")
        yield Static("Coronal Mass Ejections (past 7 days)", classes="tab-header")
        yield DataTable(id="cme-table")

    def on_mount(self) -> None:
        flare_table = self.query_one("#flare-table", DataTable)
        flare_table.add_columns("Class", "Peak Time", "Begin", "End", "Location", "Region")

        storm_table = self.query_one("#storm-table", DataTable)
        storm_table.add_columns("Start Time", "Max Kp", "Level")

        cme_table = self.query_one("#cme-table", DataTable)
        cme_table.add_columns("Start Time", "Speed (km/s)", "Type", "Half-Angle", "Location", "Region")

        self._load_data()
        self.set_interval(900, self._load_data)

    def _load_data(self) -> None:
        self._set_status("Loading...")
        self.run_worker(self._fetch_data(), exclusive=True, group="solar-fetch")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.group == "solar-fetch" and event.state == WorkerState.ERROR:
            self._set_status(f"Error: {event.worker.error}")

    async def _fetch_data(self) -> None:
        now = datetime.now(timezone.utc)
        end_date = now.strftime("%Y-%m-%d")
        flare_start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        storm_start = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        cme_start = flare_start

        errors: list[str] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                flares = await fetch_solar_flares(client, flare_start, end_date)
            except httpx.HTTPStatusError:
                flares = []
                errors.append("Flares")
            try:
                storms = await fetch_geomagnetic_storms(client, storm_start, end_date)
            except httpx.HTTPStatusError:
                storms = []
                errors.append("Storms")
            try:
                cmes = await fetch_cmes(client, cme_start, end_date)
            except httpx.HTTPStatusError:
                cmes = []
                errors.append("CMEs")

        flare_table = self.query_one("#flare-table", DataTable)
        flare_table.clear()
        for flare in reversed(flares):
            flare_table.add_row(*format_flare_row(flare))

        storm_table = self.query_one("#storm-table", DataTable)
        storm_table.clear()
        for storm in reversed(storms):
            storm_table.add_row(*format_storm_row(storm))

        cme_table = self.query_one("#cme-table", DataTable)
        cme_table.clear()
        for cme in reversed(cmes):
            cme_table.add_row(*format_cme_row(cme))

        updated = datetime.now().strftime("%H:%M:%S")
        status = f"Last updated: {updated} ({len(flares)} flares, {len(storms)} storms, {len(cmes)} CMEs)"
        if errors:
            status += f" — failed to load: {', '.join(errors)}"
        self._set_status(status)

    def action_refresh(self) -> None:
        self._load_data()

    def _set_status(self, text: str) -> None:
        self.query_one("#solar-status", Static).update(text)
