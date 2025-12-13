import flet as ft
from blackboard.ui.drawer import Drawer
from blackboard.state.app_state import AppState


def test_drawer_initialization():
    app_state = AppState()
    drawer = Drawer(app_state)

    # Should be hidden initially
    assert drawer.visible is False
    assert drawer.width == 300
    assert isinstance(drawer, ft.Container)


def test_drawer_opens_on_state_change():
    app_state = AppState()
    drawer = Drawer(app_state)
    drawer.did_mount()

    # Mock update
    drawer.update = lambda: None

    # Simulate rail click changing state
    app_state.set_active_drawer_tab("files")

    assert drawer.visible is True

    # Check content title
    # drawer.content is a Column
    column = drawer.content
    assert isinstance(column, ft.Column)

    # First item is close button row, second is title text
    title_text = column.controls[1]
    assert isinstance(title_text, ft.Text)
    assert title_text.value == "Files"


def test_drawer_content_changes():
    app_state = AppState()
    drawer = Drawer(app_state)
    drawer.did_mount()
    drawer.update = lambda: None

    # Tools tab
    app_state.set_active_drawer_tab("tools")
    title_text = drawer.content.controls[1]
    assert title_text.value == "Tool Settings"

    # Properties tab
    app_state.set_active_drawer_tab("properties")
    title_text = drawer.content.controls[1]
    assert title_text.value == "Properties"


def test_drawer_closes():
    app_state = AppState()
    drawer = Drawer(app_state)
    drawer.did_mount()
    drawer.update = lambda: None

    app_state.set_active_drawer_tab("files")
    assert drawer.visible is True

    app_state.close_drawer()
    assert drawer.visible is False
