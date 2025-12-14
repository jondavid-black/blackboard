from unittest.mock import MagicMock
import flet as ft
from blackboard.state.app_state import AppState
from blackboard.models import Path
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.ui.tools.pen_tool import PenTool
from conftest import MockStorageService


def test_pen_tool_init():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = PenTool(canvas)
    assert tool.app_state == app_state


def test_pen_tool_draw_path():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    # Set theme to light for predictable color
    app_state.theme_mode = "light"

    canvas = BlackboardCanvas(app_state)
    tool = PenTool(canvas)

    e = MagicMock()

    # Start
    tool.on_down(100, 100, e)

    current_shape = canvas.current_drawing_shape
    assert isinstance(current_shape, Path)
    assert current_shape.points == [(100, 100)]
    assert current_shape.stroke_color == ft.Colors.BLACK
    assert current_shape in app_state.shapes

    # Move to new point
    tool.on_move(101, 101, e)
    assert current_shape.points == [(100, 100), (101, 101)]

    # Move to same point (should be ignored)
    tool.on_move(101, 101, e)
    assert len(current_shape.points) == 2

    # Finish
    tool.on_up(101, 101, e)
    assert canvas.current_drawing_shape is None


def test_pen_tool_dark_mode():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.theme_mode = "dark"

    canvas = BlackboardCanvas(app_state)
    tool = PenTool(canvas)
    e = MagicMock()

    tool.on_down(100, 100, e)
    assert canvas.current_drawing_shape.stroke_color == ft.Colors.WHITE


def test_pen_tool_safety_checks():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = PenTool(canvas)
    e = MagicMock()

    # on_move with no shape
    canvas.current_drawing_shape = None
    tool.on_move(100, 100, e)  # Should not raise

    # on_move with wrong shape
    from blackboard.models import Rectangle

    canvas.current_drawing_shape = Rectangle()
    tool.on_move(100, 100, e)  # Should not raise
