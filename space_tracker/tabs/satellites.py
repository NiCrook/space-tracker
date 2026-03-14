from datetime import datetime

import httpx
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import DataTable, Static
from textual.worker import Worker, WorkerState

from space_tracker.api.celestrak import (
    SatelliteInfo,
    SatelliteStatus,
    compute_satellite_positions,
    fetch_all_satellites,
)


def format_satellite_row(sat: SatelliteInfo) -> tuple[str, ...]:
    """Format a SatelliteInfo for display in the table."""

    def fmt_deg(val: float | None) -> str:
        return f"{val:.1f}" if val is not None else "---"

    def fmt_km(val: float | None) -> str:
        return f"{val:,.0f}" if val is not None else "---"

    return (
        sat.name,
        fmt_deg(sat.altitude_deg),
        fmt_deg(sat.azimuth_deg),
        fmt_km(sat.distance_km),
        fmt_km(sat.orbital_height_km),
        sat.status.value,
        sat.next_pass_utc or "---",
    )


def format_satellite_row_styled(sat: SatelliteInfo) -> tuple:
    """Format row with styling based on visibility status."""
    raw = format_satellite_row(sat)
    if sat.status == SatelliteStatus.VISIBLE:
        return tuple(Text(cell, style="bold green") for cell in raw)
    elif sat.status == SatelliteStatus.BELOW_HORIZON:
        return tuple(Text(cell, style="dim") for cell in raw)
    return raw


def sort_satellites(satellites: list[SatelliteInfo]) -> list[SatelliteInfo]:
    """Sort: Visible first, then above horizon, then below. By altitude descending within group."""
    status_order = {
        SatelliteStatus.VISIBLE: 0,
        SatelliteStatus.ABOVE_HORIZON: 1,
        SatelliteStatus.BELOW_HORIZON: 2,
    }
    return sorted(
        satellites,
        key=lambda s: (
            status_order.get(s.status, 3),
            -(s.altitude_deg if s.altitude_deg is not None else -999),
        ),
    )


class SatellitesTab(Container):
    """Tracked satellites with position and visibility."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Static(
            "Satellites \u2014 Tracked Orbital Objects", classes="tab-header"
        )
        yield Static("", id="satellites-status")
        yield DataTable(id="satellites-table")

    def on_mount(self) -> None:
        table = self.query_one("#satellites-table", DataTable)
        table.add_columns(
            "Name",
            "Alt (\u00b0)",
            "Az (\u00b0)",
            "Distance (km)",
            "Height (km)",
            "Status",
            "Next Pass",
        )
        self._load_data()
        self.set_interval(120, self._load_data)

    def _load_data(self) -> None:
        self._set_status("Loading...")
        self.run_worker(
            self._fetch_data(), exclusive=True, group="satellites-fetch"
        )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if (
            event.worker.group == "satellites-fetch"
            and event.state == WorkerState.ERROR
        ):
            self._set_status(f"Error: {event.worker.error}")

    async def _fetch_data(self) -> None:
        location = self.app.config.location
        if location is None:
            self._set_status("Location not configured. Set your location first.")
            return

        async with httpx.AsyncClient(timeout=30.0) as client:
            omm_dicts = await fetch_all_satellites(client)

        satellites = compute_satellite_positions(
            omm_dicts,
            latitude=location.latitude,
            longitude=location.longitude,
            elevation_km=location.elevation_km,
        )

        sorted_sats = sort_satellites(satellites)
        table = self.query_one("#satellites-table", DataTable)
        table.clear()
        for sat in sorted_sats:
            table.add_row(*format_satellite_row_styled(sat))

        visible_count = sum(
            1 for s in sorted_sats if s.status == SatelliteStatus.VISIBLE
        )
        above_count = sum(
            1 for s in sorted_sats if s.status == SatelliteStatus.ABOVE_HORIZON
        )
        updated = datetime.now().strftime("%H:%M:%S")
        self._set_status(
            f"Last updated: {updated} \u2014 "
            f"{visible_count} visible, {above_count} above horizon, "
            f"{len(sorted_sats)} total"
        )

    def action_refresh(self) -> None:
        self._load_data()

    def _set_status(self, text: str) -> None:
        self.query_one("#satellites-status", Static).update(text)
