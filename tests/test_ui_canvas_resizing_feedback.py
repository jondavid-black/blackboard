import flet as ft
from unittest.mock import MagicMock
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.state.app_state import AppState
from blackboard.models import ToolType, Rectangle
from conftest import MockStorageService


def test_canvas_resize_feedback_with_shift():
    """
    Verify that when resizing a selected shape with Shift held,
    the shape (visual feedback) changes color to indicate constraint is active.
    """
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.theme_mode = "dark"  # Default color: White

    # 1. Add a rectangle
    rect = Rectangle(x=100, y=100, width=100, height=100)
    app_state.add_shape(rect)

    # 2. Select it
    app_state.set_tool(ToolType.SELECTION)
    app_state.select_shape(rect.id)

    canvas = BlackboardCanvas(app_state)
    canvas.update = lambda: None
    canvas.did_mount()  # register listener

    # 3. Start drag on Bottom-Right handle
    e_start = MagicMock(spec=ft.DragStartEvent)
    e_start.local_x = 200
    e_start.local_y = 200
    canvas.on_pan_start(e_start)

    # Verify initial color is white
    assert canvas.shapes[0].paint.color == ft.Colors.WHITE

    # 4. Press Shift
    app_state.set_shift_key(True)
    canvas._on_state_change()

    # 5. Verify color changed to CYAN (feedback)
    # canvas.shapes[0] is the rectangle.
    # canvas.shapes[1..4] are handles (because it's selected)
    # Let's verify the first shape (the rect itself)
    cv_rect = canvas.shapes[0]
    assert isinstance(cv_rect, ft.canvas.Rect)
    assert cv_rect.paint.color == ft.Colors.CYAN

    # 6. Release Shift
    app_state.set_shift_key(False)
    canvas._on_state_change()

    # 7. Verify color reverted
    assert canvas.shapes[0].paint.color == ft.Colors.WHITE
