import flet as ft
from unittest.mock import MagicMock
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.state.app_state import AppState
from blackboard.models import ToolType, Polygon
from conftest import MockStorageService


def test_polygon_tool_cleanup_and_tool_switch():
    """
    Test that PolygonTool clears current_drawing_shape on up,
    preventing crashes when switching to HandTool.
    """
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.set_tool(ToolType.POLYGON)

    canvas = BlackboardCanvas(app_state)
    canvas.update = lambda: None
    canvas.did_mount()

    # 1. Draw a polygon
    e_down = MagicMock(spec=ft.DragStartEvent)
    e_down.local_x = 100
    e_down.local_y = 100
    canvas.on_pan_start(e_down)

    assert isinstance(canvas.current_drawing_shape, Polygon)

    e_move = MagicMock(spec=ft.DragUpdateEvent)
    e_move.local_x = 200
    e_move.local_y = 200
    canvas.on_pan_update(e_move)

    e_up = MagicMock(spec=ft.DragEndEvent)
    canvas.on_pan_end(e_up)

    # CHECK: active shape should be cleared
    assert canvas.current_drawing_shape is None, (
        "PolygonTool failed to clear current_drawing_shape"
    )

    # 2. Switch to Hand Tool (this triggers _on_state_change)
    # If current_drawing_shape is not None, this might crash if HandTool doesn't handle it
    try:
        app_state.set_tool(ToolType.HAND)
    except Exception as e:
        import traceback

        traceback.print_exc()
        assert False, f"Switching to HandTool raised exception: {e}"
