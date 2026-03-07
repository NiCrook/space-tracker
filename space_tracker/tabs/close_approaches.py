from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from textual.containers import Container


class CloseApproachesTab(Container):
    """Upcoming asteroid close approaches to Earth."""

    def compose(self) -> ComposeResult:
        yield Static("Close Approaches — Upcoming Asteroid Flybys", classes="tab-header")
        yield DataTable(id="approaches-table")

    def on_mount(self) -> None:
        table = self.query_one("#approaches-table", DataTable)
        table.add_columns(
            "Object", "Date", "Distance (AU)", "Distance (LD)", "V-rel (km/s)", "Diameter"
        )
