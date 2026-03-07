from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Container


class ObjectDetailTab(Container):
    """Detailed view for a selected celestial object."""

    def compose(self) -> ComposeResult:
        yield Static("Object Detail", classes="tab-header")
        yield Static("Select an object from Sky Now or Search.", id="detail-content")
