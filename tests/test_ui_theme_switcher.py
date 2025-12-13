import flet as ft
from blackboard.state.app_state import AppState
from blackboard.ui.theme_switcher import ThemeSwitcher


def test_theme_switcher_initialization():
    app_state = AppState()
    switcher = ThemeSwitcher(app_state)

    assert isinstance(switcher, ft.Container)
    # Check initial theme mode from AppState (which defaults to "dark" in previous edits)
    assert app_state.theme_mode == "dark"


def test_theme_switcher_toggles_theme():
    app_state = AppState()
    switcher = ThemeSwitcher(app_state)
    switcher.did_mount()

    # Needs a mock update for the switcher
    switcher.update = lambda: None

    # Initial state is dark
    assert app_state.theme_mode == "dark"

    # Simulate click on the button
    # The content of ThemeSwitcher is the IconButton
    icon_button = switcher.content
    assert isinstance(icon_button, ft.IconButton)

    # Verify icon is Light Mode (sun) when in Dark Mode
    assert icon_button.icon == ft.Icons.LIGHT_MODE

    # Find the on_click handler
    click_handler = icon_button.on_click

    # Simulate click
    click_handler(None)

    # Should flip to light
    assert app_state.theme_mode == "light"

    # Verify icon changes (re-fetch content as _render_content replaces it)
    icon_button = switcher.content
    assert icon_button.icon == ft.Icons.DARK_MODE

    # Toggle back
    click_handler = icon_button.on_click
    click_handler(None)

    assert app_state.theme_mode == "dark"
