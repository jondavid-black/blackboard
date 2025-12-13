import flet as ft
from unittest.mock import MagicMock
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.state.app_state import AppState
from blackboard.models import ToolType, Rectangle
from conftest import MockStorageService


def test_canvas_shift_key_update_without_mouse_move():
    """
    Test that pressing Shift while dragging (but not moving mouse)
    updates the shape immediately.
    """
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.set_tool(ToolType.RECTANGLE)

    canvas = BlackboardCanvas(app_state)
    canvas.update = lambda: None
    canvas.did_mount()  # Hook up listeners

    # 1. Start dragging
    e_start = MagicMock(spec=ft.DragStartEvent)
    e_start.local_x = 100
    e_start.local_y = 100
    canvas.on_pan_start(e_start)

    # 2. Move to (200, 150) -> Width 100, Height 50
    e_update = MagicMock(spec=ft.DragUpdateEvent)
    e_update.local_x = 200
    e_update.local_y = 150
    canvas.on_pan_update(e_update)

    shape = app_state.shapes[0]
    assert isinstance(shape, Rectangle)
    assert shape.width == 100.0
    assert shape.height == 50.0

    # 3. Press Shift (simulate keyboard event updating state)
    # This triggers app_state.notify(), which triggers canvas._on_state_change()
    app_state.set_shift_key(True)

    # 4. Verify shape snapped to Square (100x100) WITHOUT a new PanUpdate event
    # Max dim was 100.
    assert shape.width == 100.0
    assert shape.height == 100.0

    # 5. Release Shift
    app_state.set_shift_key(False)

    # 6. Verify returns to rectangle (100x50)
    assert shape.width == 100.0
    assert shape.height == 50.0
