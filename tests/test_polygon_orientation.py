import math
from unittest.mock import MagicMock
from blackboard.state.app_state import AppState
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.ui.tools.polygon_tool import PolygonTool
from conftest import MockStorageService


def test_octagon_flat_top():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.selected_polygon_type = "octagon"

    canvas = BlackboardCanvas(app_state)
    tool = PolygonTool(canvas)
    e = MagicMock()

    # Draw at 100,100 with radius 100
    tool.on_down(100, 100, e)
    tool.on_move(100, 0, e)  # 100 up -> radius 100

    shape = canvas.current_drawing_shape
    points = shape.points

    # Points 0 and 1 should form the top edge and have same Y (min Y)
    p0 = points[0]
    p1 = points[1]

    # Allow for small floating point differences
    assert math.isclose(p0[1], p1[1], abs_tol=1e-5), (
        f"Top points Y mismatch: {p0[1]} != {p1[1]}"
    )

    # Also check they are at the top (lowest Y)
    ys = [p[1] for p in points]
    min_y = min(ys)
    assert math.isclose(p0[1], min_y, abs_tol=1e-5)


def test_hexagon_flat_top():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.selected_polygon_type = "hexagon"

    canvas = BlackboardCanvas(app_state)
    tool = PolygonTool(canvas)
    e = MagicMock()

    # Draw at 100,100 with radius 100
    tool.on_down(100, 100, e)
    tool.on_move(100, 0, e)  # 100 up -> radius 100

    shape = canvas.current_drawing_shape
    points = shape.points

    # For a flat-top hexagon, the first two points should be the top edge
    # and share the same minimal Y coordinate.

    # Let's find the points with the minimum Y
    ys = [p[1] for p in points]
    min_y = min(ys)

    # Find points close to min_y
    top_points = [p for p in points if math.isclose(p[1], min_y, abs_tol=1e-5)]

    # We expect 2 points at the top for a flat-top hexagon
    assert len(top_points) == 2, (
        f"Expected 2 top points for flat-top hexagon, found {len(top_points)}."
    )

    # Verify the two points have the same Y
    assert math.isclose(top_points[0][1], top_points[1][1], abs_tol=1e-5)
