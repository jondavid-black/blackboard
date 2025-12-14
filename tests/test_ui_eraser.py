from blackboard.state.app_state import AppState
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.models import Path, ToolType


def test_eraser_delete_shape():
    """Verify clicking a non-path shape with eraser deletes it."""
    # Use mock storage to start with clean state
    from blackboard.storage.storage_service import StorageService
    from unittest.mock import MagicMock

    mock_storage = MagicMock(spec=StorageService)
    mock_storage.load_data.return_value = ([], {})

    app_state = AppState(storage_service=mock_storage)

    # Mock update to avoid "Control must be added to page" error
    canvas = BlackboardCanvas(app_state)
    canvas.update = lambda: None

    # Add path (using Path as shape, but treating as "whole shape" delete if click)
    # Actually code deletes ANY shape on click, but "Path" triggers special drag logic.
    # If we just CLICK a path, it is deleted if we implemented that?
    # In my implementation:
    # if hit_shape is Path: we start dragging.
    # Wait, I didn't implement "click on path deletes it".
    # I implemented:
    # "If the user selects the eraser and clicks on a shape it should be deleted."
    # "If the user selects the eraser and drags over a path, delete the points that were touched."
    # My implementation starts erasing points immediately on pan_start if it is a Path.
    # So a click (pan_start + pan_end without move) on a path will erase points under cursor?
    # Yes. Which might mean splitting it or deleting it if small enough.
    # But for NON-Path shapes, it deletes immediately.

    # Let's test non-path shape deletion
    from blackboard.models import Rectangle

    rect = Rectangle(x=10, y=10, width=50, height=50)
    app_state.add_shape(rect)
    assert len(app_state.shapes) == 1

    app_state.set_tool(ToolType.ERASER)

    # Debug
    print(f"DEBUG: Shapes count before erase: {len(app_state.shapes)}")

    # Simulate Pan Start (Click)
    import flet as ft
    from unittest.mock import MagicMock

    e = MagicMock(spec=ft.DragStartEvent)
    e.local_x = 20
    e.local_y = 20  # Inside rect

    canvas.did_mount()
    canvas.on_pan_start(e)

    print(f"DEBUG: Shapes count after erase: {len(app_state.shapes)}")
    assert len(app_state.shapes) == 0


def test_eraser_path_splitting():
    """Verify dragging eraser through a path splits it."""
    # Use mock storage to start with clean state
    from blackboard.storage.storage_service import StorageService
    from blackboard.models import ToolType
    from blackboard.state.app_state import AppState
    from blackboard.ui.canvas import BlackboardCanvas
    from unittest.mock import MagicMock

    mock_storage = MagicMock(spec=StorageService)
    mock_storage.load_data.return_value = ([], {})

    app_state = AppState(storage_service=mock_storage)

    # Mock update to avoid "Control must be added to page" error
    canvas = BlackboardCanvas(app_state)
    canvas.update = lambda: None

    # Create a horizontal line path: (0,50) -> (100,50)
    points = [(float(x), 50.0) for x in range(0, 101, 10)]  # 0, 10, 20... 100
    path = Path(points=points, stroke_width=6)
    app_state.add_shape(path)

    app_state.set_tool(ToolType.ERASER)
    canvas.did_mount()

    # Drag through the middle (around x=50)
    import flet as ft
    from unittest.mock import MagicMock

    # Start eraser
    e_start = MagicMock(spec=ft.DragStartEvent)
    e_start.local_x = 50.0
    e_start.local_y = 50.0

    # DEBUG: Check initial state
    print(f"DEBUG: Path points before: {path.points}")
    print("DEBUG: Eraser at 50,50. Radius 10.")

    canvas.on_pan_start(e_start)

    # DEBUG: Check state after
    print(f"DEBUG: Shapes count: {len(app_state.shapes)}")
    if len(app_state.shapes) > 0:
        print(f"DEBUG: Shape 0 points: {app_state.shapes[0].points}")
    if len(app_state.shapes) > 1:
        print(f"DEBUG: Shape 1 points: {app_state.shapes[1].points}")

    assert len(app_state.shapes) == 2
    path1 = app_state.shapes[0]
    path2 = app_state.shapes[1]

    assert len(path1.points) > 0
    assert len(path2.points) > 0

    # Verify separation
    # One path should end <= 40
    # Other start >= 60

    # Note: app_state.shapes order might preserve original at index 0?
    # My code updates original path with first segment, adds new paths for others.

    # Path1 (original) should be the left one (0..40)
    p1_xs = [p[0] for p in path1.points]
    assert max(p1_xs) <= 45

    # Path2 (new) should be the right one (60..100)
    p2_xs = [p[0] for p in path2.points]
    assert min(p2_xs) >= 55
