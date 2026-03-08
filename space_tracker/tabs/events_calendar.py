from datetime import date, datetime, timedelta

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import DataTable, Static
from textual.worker import Worker, WorkerState

from space_tracker.api.events import CelestialEvent, get_all_events


def format_event_row(event: CelestialEvent) -> tuple[str, ...]:
    type_label = event.event_type.value

    if event.date_end and event.date_end != event.date_peak:
        date_str = (
            f"{event.date_peak.strftime('%b %d')} - {event.date_end.strftime('%b %d')}"
        )
    else:
        date_str = event.date_peak.strftime("%b %d")

    today = date.today()
    delta = (event.date_peak - today).days
    if delta == 0:
        when = "TODAY"
    elif delta == 1:
        when = "in 1d"
    elif delta > 1:
        when = f"in {delta}d"
    elif delta == -1:
        when = "1d ago"
    else:
        when = f"{-delta}d ago"

    return (type_label, event.name, date_str, when, event.description)


class EventsCalendarTab(Container):
    """Upcoming astronomical events: conjunctions, oppositions, meteor showers, eclipses."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("Events Calendar — Astronomical Events", classes="tab-header")
        yield Static("", id="events-status")
        yield DataTable(id="events-table")

    def on_mount(self) -> None:
        table = self.query_one("#events-table", DataTable)
        table.add_columns("Type", "Event", "Date", "When", "Details")
        self._load_data()
        self.set_interval(3600, self._load_data)

    def _load_data(self) -> None:
        self._set_status("Loading...")
        self.run_worker(self._compute_events(), exclusive=True, group="events-fetch")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.group == "events-fetch" and event.state == WorkerState.ERROR:
            self._set_status(f"Error: {event.worker.error}")

    async def _compute_events(self) -> None:
        today = date.today()
        current_year = today.year
        cutoff_past = today - timedelta(days=30)

        events = get_all_events(current_year)
        if today.month >= 10:
            events = events + get_all_events(current_year + 1)

        filtered = [e for e in events if e.date_peak >= cutoff_past]
        filtered.sort(key=lambda e: e.date_peak)

        table = self.query_one("#events-table", DataTable)
        table.clear()
        for ev in filtered:
            table.add_row(*format_event_row(ev))

        updated = datetime.now().strftime("%H:%M:%S")
        self._set_status(f"Last updated: {updated} ({len(filtered)} events)")

    def action_refresh(self) -> None:
        self._load_data()

    def _set_status(self, text: str) -> None:
        self.query_one("#events-status", Static).update(text)
