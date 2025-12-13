import flet as ft
from unittest.mock import MagicMock
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.state.app_state import AppState
from blackboard.models import ToolType, Line
from conftest import MockStorageService


def test_canvas_drawing_colors_dark_mode():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.theme_mode = "dark"
    app_state.set_tool(ToolType.LINE)
    canvas = BlackboardCanvas(app_state)

    # Mock update
    canvas.update = lambda: None

    # Start drawing
    e = MagicMock(spec=ft.DragStartEvent)
    e.local_x = 100
    e.local_y = 100
    canvas.on_pan_start(e)

    assert len(app_state.shapes) == 1
    shape = app_state.shapes[0]

    # New shapes should have explicit color set based on theme
    assert shape.stroke_color == ft.Colors.WHITE

    # Render and check paint color
    canvas._on_state_change()

    # Check that the paint color used for rendering is correct
    # We can inspect the flet_canvas.Line object in canvas.shapes
    assert len(canvas.shapes) == 1
    cv_line = canvas.shapes[0]
    assert cv_line.paint.color == ft.Colors.WHITE


def test_canvas_drawing_colors_light_mode():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.theme_mode = "light"
    app_state.set_tool(ToolType.LINE)
    canvas = BlackboardCanvas(app_state)

    # Mock update
    canvas.update = lambda: None

    # Start drawing
    e = MagicMock(spec=ft.DragStartEvent)
    e.local_x = 100
    e.local_y = 100
    canvas.on_pan_start(e)

    shape = app_state.shapes[0]
    assert shape.stroke_color == ft.Colors.BLACK

    # Render
    canvas._on_state_change()
    cv_line = canvas.shapes[0]
    assert cv_line.paint.color == ft.Colors.BLACK


def test_canvas_renders_empty_color_correctly():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.theme_mode = "dark"
    canvas = BlackboardCanvas(app_state)
    canvas.update = lambda: None

    # Use Line subclass to ensure it renders
    line = Line(x=0, y=0, end_x=10, end_y=10, stroke_color="")
    app_state.add_shape(line)

    canvas._on_state_change()

    cv_line = canvas.shapes[0]
    # Should default to White in Dark mode
    assert cv_line.paint.color == ft.Colors.WHITE

    # Switch to Light mode
    app_state.theme_mode = "light"
    canvas._on_state_change()

    cv_line = canvas.shapes[0]
    # Should default to Black in Light mode
    assert cv_line.paint.color == ft.Colors.BLACK
