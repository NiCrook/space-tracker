from datetime import datetime, timedelta, timezone

import httpx
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Static
from textual.containers import Container
from textual.worker import Worker, WorkerState

from space_tracker.api.horizons import (
    EphemerisRow,
    RiseTransitSet,
    compute_rise_transit_set,
    fetch_ephemeris,
)


def format_detail(
    name: str, row: EphemerisRow, rts: RiseTransitSet
) -> str:
    """Build Rich markup text for the detail view."""

    def fmt(val: float | None, fmt_str: str = ".1f") -> str:
        return f"{val:{fmt_str}}" if val is not None else "---"

    lines = [
        f"[bold]── {name} ──────────────────────[/bold]",
        "",
        "[bold]Position[/bold]",
        f"  RA:  {row.ra}    Dec: {row.dec}",
        f"  Alt: {fmt(row.elevation):<14s} Az:  {fmt(row.azimuth)}",
        "",
        "[bold]Properties[/bold]",
        f"  Magnitude:    {fmt(row.magnitude)}",
        f"  Distance:     {fmt(row.delta_au, '.4f')} AU",
        f"  Elongation:   {fmt(row.solar_elongation)}",
        "",
        "[bold]Rise / Transit / Set[/bold]",
        f"  Rise:    {rts.rise or '---'}",
    ]

    if rts.transit and rts.transit_elevation is not None:
        lines.append(f"  Transit: {rts.transit} (alt {rts.transit_elevation:.1f})")
    else:
        lines.append(f"  Transit: {rts.transit or '---'}")

    lines.append(f"  Set:     {rts.set_time or '---'}")

    return "\n".join(lines)


class ObjectDetailTab(Container):
    """Detailed view for a selected celestial object."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._object_name: str | None = None
        self._object_command: str | None = None

    def compose(self) -> ComposeResult:
        yield Static("Object Detail", classes="tab-header")
        yield Static("", id="detail-status")
        yield Static("Select an object from Sky Now or Search.", id="detail-content")

    def load_object(self, name: str, command: str) -> None:
        """Load detail for the given object. Called by the app."""
        self._object_name = name
        self._object_command = command
        self._set_status("Loading...")
        self.run_worker(self._fetch_detail(), exclusive=True, group="detail-fetch")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.group == "detail-fetch" and event.state == WorkerState.ERROR:
            self._set_status(f"Error: {event.worker.error}")

    async def _fetch_detail(self) -> None:
        location = self.app.config.location
        if location is None:
            self._set_status("Location not configured.")
            return

        name = self._object_name
        command = self._object_command
        if not name or not command:
            return

        now = datetime.now(timezone.utc)
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Current snapshot
            start = now.strftime("%Y-%b-%d %H:%M")
            stop = (now + timedelta(minutes=1)).strftime("%Y-%b-%d %H:%M")
            snapshot_rows = await fetch_ephemeris(
                client, command, location, start, stop, step_size="1 min"
            )

            # 24-hour ephemeris for rise/set
            rts_start = (now - timedelta(hours=2)).strftime("%Y-%b-%d %H:%M")
            rts_stop = (now + timedelta(hours=22)).strftime("%Y-%b-%d %H:%M")
            rts_rows = await fetch_ephemeris(
                client, command, location, rts_start, rts_stop, step_size="10 min"
            )

        if not snapshot_rows:
            self._set_status("No data returned from Horizons.")
            return

        rts = compute_rise_transit_set(rts_rows)
        content = format_detail(name, snapshot_rows[0], rts)
        self.query_one("#detail-content", Static).update(content)

        updated = datetime.now().strftime("%H:%M:%S")
        self._set_status(f"Last updated: {updated}")

    def action_refresh(self) -> None:
        if self._object_name and self._object_command:
            self.load_object(self._object_name, self._object_command)

    def _set_status(self, text: str) -> None:
        self.query_one("#detail-status", Static).update(text)
