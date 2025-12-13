import flet as ft
from unittest.mock import MagicMock
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.state.app_state import AppState
from blackboard.models import ToolType, Rectangle, Line
from conftest import MockStorageService


def test_canvas_resize_rectangle_bottom_right():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)

    # 1. Add a rectangle
    rect = Rectangle(x=100, y=100, width=100, height=100)
    app_state.add_shape(rect)

    # 2. Select it
    app_state.set_tool(ToolType.SELECTION)
    app_state.select_shape(rect.id)

    canvas = BlackboardCanvas(app_state)
    canvas.update = lambda: None

    # 3. Start drag on Bottom-Right handle
    # Handle should be at (x+w, y+h) -> (200, 200)
    e_start = MagicMock(spec=ft.DragStartEvent)
    e_start.local_x = 200
    e_start.local_y = 200
    canvas.on_pan_start(e_start)

    # 4. Drag to (250, 250)
    e_update = MagicMock(spec=ft.DragUpdateEvent)
    e_update.local_x = 250
    e_update.local_y = 250
    canvas.on_pan_update(e_update)

    # Check that width/height increased
    assert rect.width == 150.0
    assert rect.height == 150.0
    # Origin should not change for bottom-right drag
    assert rect.x == 100.0
    assert rect.y == 100.0


def test_canvas_resize_rectangle_top_left():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)

    rect = Rectangle(x=100, y=100, width=100, height=100)
    app_state.add_shape(rect)
    app_state.set_tool(ToolType.SELECTION)
    app_state.select_shape(rect.id)

    canvas = BlackboardCanvas(app_state)
    canvas.update = lambda: None

    # Start drag on Top-Left handle (100, 100)
    e_start = MagicMock(spec=ft.DragStartEvent)
    e_start.local_x = 100
    e_start.local_y = 100
    canvas.on_pan_start(e_start)

    # Drag to (50, 50) -> Should expand rect to the top-left
    e_update = MagicMock(spec=ft.DragUpdateEvent)
    e_update.local_x = 50
    e_update.local_y = 50
    canvas.on_pan_update(e_update)

    # New x,y should be 50, 50
    assert rect.x == 50.0
    assert rect.y == 50.0
    # Width/Height should increase by 50
    assert rect.width == 150.0
    assert rect.height == 150.0


def test_canvas_resize_line_endpoint():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)

    line = Line(x=100, y=100, end_x=200, end_y=200)
    app_state.add_shape(line)
    app_state.set_tool(ToolType.SELECTION)
    app_state.select_shape(line.id)

    canvas = BlackboardCanvas(app_state)
    canvas.update = lambda: None

    # Start drag on End Point (200, 200)
    e_start = MagicMock(spec=ft.DragStartEvent)
    e_start.local_x = 200
    e_start.local_y = 200
    canvas.on_pan_start(e_start)

    # Drag to (250, 250)
    e_update = MagicMock(spec=ft.DragUpdateEvent)
    e_update.local_x = 250
    e_update.local_y = 250
    canvas.on_pan_update(e_update)

    assert line.end_x == 250.0
    assert line.end_y == 250.0
    # Start point unchanged
    assert line.x == 100.0
    assert line.y == 100.0
