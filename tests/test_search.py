from unittest.mock import MagicMock

from space_tracker.tabs.search import SearchTab, _resolve_command


def test_resolve_command_known_planet():
    """Known planet names resolve to their numeric Horizons ID."""
    assert _resolve_command("Mars") == ("Mars", "499")
    assert _resolve_command("mars") == ("Mars", "499")
    assert _resolve_command("JUPITER") == ("Jupiter", "599")


def test_resolve_command_unknown_uses_raw_query():
    """Unknown queries pass through as-is."""
    assert _resolve_command("Ceres") == ("Ceres", "Ceres")
    assert _resolve_command("433") == ("433", "433")


def test_empty_input_does_not_search():
    """Verify that on_input_submitted ignores empty/whitespace input."""
    tab = SearchTab()
    tab._do_search = MagicMock()

    # Simulate an Input.Submitted event with empty value
    event = MagicMock()
    event.value = "   "
    tab.on_input_submitted(event)

    tab._do_search.assert_not_called()


def test_non_empty_input_triggers_search():
    """Verify that on_input_submitted calls _do_search for valid input."""
    tab = SearchTab()
    tab._do_search = MagicMock()

    event = MagicMock()
    event.value = "Mars"
    tab.on_input_submitted(event)

    tab._do_search.assert_called_once_with("Mars")


def test_last_query_stored():
    """Verify that _do_search stores the query for refresh."""
    tab = SearchTab()
    tab.query_one = MagicMock()
    tab.run_worker = MagicMock()

    tab._do_search("Ceres")

    assert tab._last_query == "Ceres"


def test_action_refresh_without_query():
    """Verify that refresh with no prior query is a no-op."""
    tab = SearchTab()
    tab._do_search = MagicMock()

    tab.action_refresh()

    tab._do_search.assert_not_called()


def test_action_refresh_with_prior_query():
    """Verify that refresh re-runs the last query."""
    tab = SearchTab()
    tab._last_query = "433"
    tab._do_search = MagicMock()

    tab.action_refresh()

    tab._do_search.assert_called_once_with("433")
