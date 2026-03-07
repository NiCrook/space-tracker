from datetime import datetime, timedelta, timezone

import httpx
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Static
from textual.containers import Container
from textual.worker import Worker, WorkerState

from space_tracker.api.close_approaches import CloseApproach, fetch_close_approaches


def format_approach_row(ca: CloseApproach) -> tuple[str, ...]:
    """Format a CloseApproach for display in the table."""
    if ca.diameter_min_m is not None and ca.diameter_max_m is not None:
        if ca.diameter_max_m >= 1000:
            diameter = f"{ca.diameter_min_m / 1000:.1f}–{ca.diameter_max_m / 1000:.1f} km"
        else:
            diameter = f"{ca.diameter_min_m:.0f}–{ca.diameter_max_m:.0f} m"
    else:
        diameter = "---"

    return (
        ca.fullname,
        ca.close_approach_date,
        f"{ca.distance_au:.5f}",
        f"{ca.distance_ld:.2f}",
        f"{ca.v_rel:.1f}",
        diameter,
    )


class CloseApproachesTab(Container):
    """Upcoming asteroid close approaches to Earth."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("Close Approaches — Upcoming Asteroid Flybys", classes="tab-header")
        yield Static("", id="approaches-status")
        yield DataTable(id="approaches-table")

    def on_mount(self) -> None:
        table = self.query_one("#approaches-table", DataTable)
        table.add_columns(
            "Object", "Date", "Distance (AU)", "Distance (LD)", "V-rel (km/s)", "Diameter"
        )
        self._load_data()
        self.set_interval(900, self._load_data)

    def _load_data(self) -> None:
        self._set_status("Loading...")
        self.run_worker(self._fetch_data(), exclusive=True, group="approaches-fetch")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.group == "approaches-fetch" and event.state == WorkerState.ERROR:
            self._set_status(f"Error: {event.worker.error}")

    async def _fetch_data(self) -> None:
        now = datetime.now(timezone.utc)
        date_min = now.strftime("%Y-%m-%d")
        date_max = (now + timedelta(days=60)).strftime("%Y-%m-%d")

        async with httpx.AsyncClient(timeout=30.0) as client:
            approaches = await fetch_close_approaches(
                client, date_min=date_min, date_max=date_max
            )

        table = self.query_one("#approaches-table", DataTable)
        table.clear()
        for ca in approaches:
            table.add_row(*format_approach_row(ca))

        updated = datetime.now().strftime("%H:%M:%S")
        self._set_status(f"Last updated: {updated} ({len(approaches)} approaches)")

    def action_refresh(self) -> None:
        self._load_data()

    def _set_status(self, text: str) -> None:
        self.query_one("#approaches-status", Static).update(text)
