from textual.app import ComposeResult
from textual.widgets import Input, Static
from textual.containers import Container


class SearchTab(Container):
    """Search for any celestial object by name or designation."""

    def compose(self) -> ComposeResult:
        yield Static("Search — Find an Object", classes="tab-header")
        yield Input(placeholder="Enter object name or designation (e.g., Mars, Ceres, 433)", id="search-input")
        yield Static("", id="search-results")
