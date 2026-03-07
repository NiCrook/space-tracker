from datetime import datetime, timedelta, timezone

import httpx
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widgets import DataTable, Static
from textual.containers import Container
from textual.worker import Worker, WorkerState

from space_tracker.api.horizons import PLANET_COMMANDS, EphemerisRow


def format_row(name: str, row: EphemerisRow) -> tuple[str, ...]:
    """Format an EphemerisRow for display in the table."""

    def fmt_deg(val: float | None) -> str:
        return f"{val:.1f}" if val is not None else "---"

    def fmt_mag(val: float | None) -> str:
        return f"{val:.1f}" if val is not None else "---"

    def fmt_au(val: float | None) -> str:
        return f"{val:.4f}" if val is not None else "---"

    return (
        name,
        fmt_deg(row.elevation),
        fmt_deg(row.azimuth),
        fmt_mag(row.magnitude),
        row.ra,
        row.dec,
        fmt_au(row.delta_au),
        fmt_deg(row.solar_elongation),
    )


def sort_rows(rows: list[tuple[str, EphemerisRow]]) -> list[tuple[str, EphemerisRow]]:
    """Sort by altitude descending, None values last."""
    return sorted(
        rows,
        key=lambda item: item[1].elevation if item[1].elevation is not None else -999,
        reverse=True,
    )


class SkyNowTab(Container):
    """Objects currently visible from the user's location."""

    class ObjectSelected(Message):
        """Posted when a user selects a row in the sky table."""

        def __init__(self, name: str, command: str) -> None:
            super().__init__()
            self.name = name
            self.command = command

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("Sky Now — Visible Objects", classes="tab-header")
        yield Static("", id="sky-status")
        yield DataTable(id="sky-table")

    def on_mount(self) -> None:
        table = self.query_one("#sky-table", DataTable)
        table.add_columns(
            "Name", "Alt", "Az", "Mag", "RA", "Dec", "Distance (AU)", "Elongation"
        )
        self._load_data()
        self.set_interval(300, self._load_data)

    def _load_data(self) -> None:
        self._set_status("Loading...")
        self.run_worker(self._fetch_all(), exclusive=True, group="sky-fetch")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.group == "sky-fetch" and event.state == WorkerState.ERROR:
            self._set_status(f"Error: {event.worker.error}")

    async def _fetch_all(self) -> None:
        location = self.app.config.location
        if location is None:
            self._set_status("Location not configured. Set your location first.")
            return

        now = datetime.now(timezone.utc)
        start = now.strftime("%Y-%b-%d %H:%M")
        stop = (now + timedelta(minutes=1)).strftime("%Y-%b-%d %H:%M")

        results: list[tuple[str, EphemerisRow]] = []
        cache = self.app.cache

        async with httpx.AsyncClient(timeout=30.0) as client:
            batch = await cache.fetch_batch(
                client, PLANET_COMMANDS, location, start, stop, step_size="1 min"
            )
            for name, rows in batch.items():
                if rows:
                    results.append((name, rows[0]))

        sorted_results = sort_rows(results)
        self._results = sorted_results

        table = self.query_one("#sky-table", DataTable)
        table.clear()
        table.cursor_type = "row"
        for name, row in sorted_results:
            table.add_row(*format_row(name, row))

        updated = datetime.now().strftime("%H:%M:%S")
        self._set_status(f"Last updated: {updated} ({len(results)} objects)")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if not hasattr(self, "_results") or not self._results:
            return
        row_index = event.cursor_row
        if 0 <= row_index < len(self._results):
            name = self._results[row_index][0]
            command = PLANET_COMMANDS.get(name, "")
            if command:
                self.post_message(self.ObjectSelected(name, command))

    def action_refresh(self) -> None:
        self._load_data()

    def _set_status(self, text: str) -> None:
        self.query_one("#sky-status", Static).update(text)
