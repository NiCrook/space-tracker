from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane

from space_tracker.config import Config
from space_tracker.screens.location_setup import LocationSetupScreen
from space_tracker.tabs.sky_now import SkyNowTab
from space_tracker.tabs.object_detail import ObjectDetailTab
from space_tracker.tabs.close_approaches import CloseApproachesTab
from space_tracker.tabs.search import SearchTab


class SpaceTrackerApp(App):
    """A TUI for amateur astronomers to track celestial objects."""

    TITLE = "Space Tracker"
    CSS = """
    .tab-header {
        text-style: bold;
        padding: 1 2;
        color: $accent;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config = Config.load()

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Sky Now", id="tab-sky-now"):
                yield SkyNowTab()
            with TabPane("Object Detail", id="tab-object-detail"):
                yield ObjectDetailTab()
            with TabPane("Close Approaches", id="tab-close-approaches"):
                yield CloseApproachesTab()
            with TabPane("Search", id="tab-search"):
                yield SearchTab()
        yield Footer()

    def on_mount(self) -> None:
        if self.config.location is None:
            self.push_screen(LocationSetupScreen(self.config))


def main() -> None:
    app = SpaceTrackerApp()
    app.run()


if __name__ == "__main__":
    main()
