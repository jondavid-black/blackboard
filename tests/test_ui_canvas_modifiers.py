import flet as ft
from unittest.mock import MagicMock
import math
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.state.app_state import AppState
from blackboard.models import ToolType, Rectangle, Line
from conftest import MockStorageService


def test_canvas_draw_rectangle_with_shift_forces_square():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.set_tool(ToolType.RECTANGLE)
    app_state.set_shift_key(True)

    canvas = BlackboardCanvas(app_state)
    canvas.update = lambda: None

    # 1. Start drawing at (100, 100)
    e_start = MagicMock(spec=ft.DragStartEvent)
    e_start.local_x = 100
    e_start.local_y = 100
    canvas.on_pan_start(e_start)

    # 2. Drag to (150, 200) -> Width 50, Height 100
    # With Shift, should take max dimension (100) -> 100x100 square
    e_update = MagicMock(spec=ft.DragUpdateEvent)
    e_update.local_x = 150
    e_update.local_y = 200
    canvas.on_pan_update(e_update)

    shape = app_state.shapes[0]
    assert isinstance(shape, Rectangle)
    assert shape.width == 100.0
    assert shape.height == 100.0

    # 3. Drag to negative direction (50, 80) -> dx = -50, dy = -20
    # Max dim is 50. Should be -50, -50
    e_update.local_x = 50
    e_update.local_y = 80
    canvas.on_pan_update(e_update)

    assert shape.width == -50.0
    assert shape.height == -50.0


def test_canvas_draw_line_with_shift_snaps_angle():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.set_tool(ToolType.LINE)
    app_state.set_shift_key(True)

    canvas = BlackboardCanvas(app_state)
    canvas.update = lambda: None

    # Start at 100, 100
    e_start = MagicMock(spec=ft.DragStartEvent)
    e_start.local_x = 100
    e_start.local_y = 100
    canvas.on_pan_start(e_start)

    # Drag to 200, 110. (dx=100, dy=10)
    # Angle is close to 0. Should snap to 0 (horizontal).
    # Length is approx 100.5
    e_update = MagicMock(spec=ft.DragUpdateEvent)
    e_update.local_x = 200
    e_update.local_y = 110
    canvas.on_pan_update(e_update)

    shape = app_state.shapes[0]
    assert isinstance(shape, Line)

    # Expected: y should stay close to 100 (horizontal line)
    # x should be around 200
    assert math.isclose(shape.end_y, 100.0, abs_tol=0.1)
    assert shape.end_x > 190.0

    # Drag to 200, 210 (dx=100, dy=110)
    # Angle is close to 45 deg. Should snap to 45.
    # 45 deg means dx = dy.
    e_update.local_x = 200
    e_update.local_y = 210
    canvas.on_pan_update(e_update)

    dx = shape.end_x - shape.x
    dy = shape.end_y - shape.y
    assert math.isclose(dx, dy, abs_tol=0.1)

    # Drag to 100, 200 (dx=0, dy=100) - Vertical
    e_update.local_x = 105
    e_update.local_y = 200
    canvas.on_pan_update(e_update)

    assert math.isclose(shape.end_x, 100.0, abs_tol=0.1)
    assert shape.end_y > 190.0
