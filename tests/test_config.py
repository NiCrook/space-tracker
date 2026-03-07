import json

from space_tracker.config import Config, Location


def test_config_save_load_roundtrip(tmp_path, monkeypatch) -> None:
    config_dir = tmp_path / ".config" / "space-tracker"
    config_file = config_dir / "config.json"

    monkeypatch.setattr("space_tracker.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("space_tracker.config.CONFIG_FILE", config_file)

    config = Config(location=Location(latitude=30.27, longitude=-97.74, elevation_km=0.15))
    config.save()

    loaded = Config.load()
    assert loaded.location is not None
    assert loaded.location.latitude == 30.27
    assert loaded.location.longitude == -97.74
    assert loaded.location.elevation_km == 0.15


def test_config_load_missing_file(tmp_path, monkeypatch) -> None:
    config_file = tmp_path / "nonexistent" / "config.json"
    monkeypatch.setattr("space_tracker.config.CONFIG_FILE", config_file)

    config = Config.load()
    assert config.location is None


def test_config_save_without_location(tmp_path, monkeypatch) -> None:
    config_dir = tmp_path / ".config" / "space-tracker"
    config_file = config_dir / "config.json"

    monkeypatch.setattr("space_tracker.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("space_tracker.config.CONFIG_FILE", config_file)

    config = Config()
    config.save()

    data = json.loads(config_file.read_text())
    assert data == {}

    loaded = Config.load()
    assert loaded.location is None


def test_config_load_missing_elevation(tmp_path, monkeypatch) -> None:
    config_dir = tmp_path / ".config" / "space-tracker"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True)

    monkeypatch.setattr("space_tracker.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("space_tracker.config.CONFIG_FILE", config_file)

    config_file.write_text(json.dumps({
        "location": {"latitude": 40.0, "longitude": -74.0}
    }))

    loaded = Config.load()
    assert loaded.location is not None
    assert loaded.location.elevation_km == 0.0
