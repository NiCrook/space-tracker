from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from textual.containers import Container


class SkyNowTab(Container):
    """Objects currently visible from the user's location."""

    def compose(self) -> ComposeResult:
        yield Static("Sky Now — Visible Objects", classes="tab-header")
        yield DataTable(id="sky-table")

    def on_mount(self) -> None:
        table = self.query_one("#sky-table", DataTable)
        table.add_columns(
            "Name", "Alt", "Az", "Mag", "RA", "Dec", "Distance (AU)", "Elongation"
        )
