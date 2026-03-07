import httpx
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from space_tracker.api.geolocation import GeoResult, detect_location
from space_tracker.config import Config, Location


class LocationSetupScreen(Screen):
    """First-run screen to configure the user's location."""

    CSS = """
    #location-container {
        width: 60;
        height: auto;
        margin: 2 0;
        padding: 1 2;
        border: round $accent;
    }
    #status-label {
        margin: 1 0;
        text-style: italic;
        color: $text-muted;
    }
    #detected-info {
        margin: 1 0;
    }
    .form-field {
        margin: 1 0;
    }
    #button-row {
        layout: horizontal;
        height: 3;
        margin: 1 0;
    }
    #button-row Button {
        margin: 0 1;
    }
    """

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self._geo_result: GeoResult | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Center():
            with Vertical(id="location-container"):
                yield Static("Location Setup", classes="tab-header")
                yield Label("Detecting your location...", id="status-label")
                yield Label("", id="detected-info")
                yield Input(
                    placeholder="Latitude (e.g. 30.27)",
                    id="input-lat",
                    classes="form-field",
                )
                yield Input(
                    placeholder="Longitude (e.g. -97.74)",
                    id="input-lon",
                    classes="form-field",
                )
                yield Input(
                    placeholder="Elevation in km (default: 0.0)",
                    id="input-elev",
                    classes="form-field",
                )
                with Center(id="button-row"):
                    yield Button("Accept", id="btn-accept", variant="primary")
                    yield Button("Edit Manually", id="btn-edit", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self._hide_form()
        self.query_one("#btn-accept", Button).display = False
        self.query_one("#btn-edit", Button).display = False
        self._detect_location()

    def _hide_form(self) -> None:
        for widget_id in ("#input-lat", "#input-lon", "#input-elev"):
            self.query_one(widget_id, Input).display = False

    def _show_form(self) -> None:
        for widget_id in ("#input-lat", "#input-lon", "#input-elev"):
            self.query_one(widget_id, Input).display = True

    @work(exclusive=True)
    async def _detect_location(self) -> None:
        async with httpx.AsyncClient() as client:
            result = await detect_location(client)

        if result:
            self._geo_result = result
            loc = result.location
            self.query_one("#status-label", Label).update("Location detected:")
            self.query_one("#detected-info", Label).update(
                f"{result.display_name} ({loc.latitude:.4f}, {loc.longitude:.4f})"
            )
            self.query_one("#btn-accept", Button).display = True
            self.query_one("#btn-edit", Button).display = True
        else:
            self.query_one("#status-label", Label).update(
                "Could not detect location. Please enter manually:"
            )
            self.query_one("#detected-info", Label).update("")
            self._show_form()
            self.query_one("#btn-accept", Button).display = True
            self.query_one("#btn-accept", Button).label = "Save"

    @on(Button.Pressed, "#btn-accept")
    def _on_accept(self) -> None:
        if self._geo_result and not self.query_one("#input-lat", Input).display:
            self.config.location = self._geo_result.location
        else:
            location = self._parse_form()
            if location is None:
                return
            self.config.location = location
        self.config.save()
        self.dismiss()

    @on(Button.Pressed, "#btn-edit")
    def _on_edit(self) -> None:
        self._show_form()
        if self._geo_result:
            loc = self._geo_result.location
            self.query_one("#input-lat", Input).value = str(loc.latitude)
            self.query_one("#input-lon", Input).value = str(loc.longitude)
        self.query_one("#btn-edit", Button).display = False
        self.query_one("#btn-accept", Button).label = "Save"

    def _parse_form(self) -> Location | None:
        try:
            lat = float(self.query_one("#input-lat", Input).value)
            lon = float(self.query_one("#input-lon", Input).value)
        except ValueError:
            self.query_one("#status-label", Label).update(
                "Invalid latitude or longitude. Please enter numeric values."
            )
            return None

        elev_str = self.query_one("#input-elev", Input).value.strip()
        try:
            elev = float(elev_str) if elev_str else 0.0
        except ValueError:
            self.query_one("#status-label", Label).update(
                "Invalid elevation. Please enter a numeric value."
            )
            return None

        return Location(latitude=lat, longitude=lon, elevation_km=elev)
