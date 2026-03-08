from datetime import datetime, timedelta, timezone

import httpx
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Input, Static
from textual.containers import Container
from textual.worker import Worker, WorkerState

from space_tracker.api.horizons import PLANET_COMMANDS, compute_rise_transit_set
from space_tracker.tabs.object_detail import format_detail


def _resolve_command(query: str) -> tuple[str, str]:
    """Resolve a user query to a (display_name, horizons_command) pair.

    Checks PLANET_COMMANDS (case-insensitive) first so common names like
    "Mars" map to their numeric ID ('499') instead of triggering Horizons'
    disambiguation prompt.  Falls back to using the raw query as-is.
    """
    lookup = {k.lower(): (k, v) for k, v in PLANET_COMMANDS.items()}
    match = lookup.get(query.lower())
    if match:
        return match
    return (query, query)


class SearchTab(Container):
    """Search for any celestial object by name or designation."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._last_query: str | None = None

    def compose(self) -> ComposeResult:
        yield Static("Search — Find an Object", classes="tab-header")
        yield Input(placeholder="Enter object name or designation (e.g., Mars, Ceres, 433)", id="search-input")
        yield Static("", id="search-status")
        yield Static("", id="search-results")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        self._do_search(query)

    def _do_search(self, query: str) -> None:
        self._last_query = query
        self._set_status(f"Searching for '{query}'...")
        self.query_one("#search-results", Static).update("")
        self.run_worker(self._fetch_results(query), exclusive=True, group="search-fetch")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.group == "search-fetch" and event.state == WorkerState.ERROR:
            self._set_status(f"Error: {event.worker.error}")

    async def _fetch_results(self, query: str) -> None:
        location = self.app.config.location
        if location is None:
            self._set_status("Location not configured.")
            return

        name, command = _resolve_command(query)
        now = datetime.now(timezone.utc)
        cache = self.app.cache

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Current snapshot
            start = now.strftime("%Y-%b-%d %H:%M")
            stop = (now + timedelta(minutes=1)).strftime("%Y-%b-%d %H:%M")
            snapshot_rows = await cache.fetch(
                client, command, location, start, stop, step_size="1 min"
            )

            # 24-hour ephemeris for rise/set
            rts_start = (now - timedelta(hours=2)).strftime("%Y-%b-%d %H:%M")
            rts_stop = (now + timedelta(hours=22)).strftime("%Y-%b-%d %H:%M")
            rts_rows = await cache.fetch(
                client, command, location, rts_start, rts_stop,
                step_size="10 min", ttl=600.0,
            )

        if not snapshot_rows:
            self._set_status(f"No data returned for '{query}'.")
            return

        rts = compute_rise_transit_set(rts_rows)
        content = format_detail(name, snapshot_rows[0], rts)
        self.query_one("#search-results", Static).update(content)

        updated = datetime.now().strftime("%H:%M:%S")
        self._set_status(f"Last updated: {updated}")

    def action_refresh(self) -> None:
        if self._last_query:
            self._do_search(self._last_query)

    def _set_status(self, text: str) -> None:
        self.query_one("#search-status", Static).update(text)
