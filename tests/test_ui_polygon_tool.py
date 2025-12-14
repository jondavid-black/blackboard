import math
from unittest.mock import MagicMock
from blackboard.state.app_state import AppState
from blackboard.models import Polygon
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.ui.tools.polygon_tool import PolygonTool
from conftest import MockStorageService


def test_polygon_tool_init():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = PolygonTool(canvas)
    assert tool.app_state == app_state


def test_polygon_tool_draw_triangle():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    # Default is triangle
    app_state.selected_polygon_type = "triangle"

    canvas = BlackboardCanvas(app_state)
    tool = PolygonTool(canvas)

    e = MagicMock()

    # Start at 100, 100
    tool.on_down(100, 100, e)

    current_shape = canvas.current_drawing_shape
    assert isinstance(current_shape, Polygon)
    assert current_shape.x == 100
    assert current_shape.y == 100
    assert current_shape.polygon_type == "triangle"
    assert len(current_shape.points) == 0

    # Drag to 150, 150 (rx=50, ry=50)
    tool.on_move(150, 150, e)

    # Triangle has 3 points
    assert len(current_shape.points) == 3

    # Verify points generation logic roughly
    # Base logic: cx + rx * cos(angle), cy + ry * sin(angle)
    # Start angle -pi/2 (top)
    # For triangle: -90 deg (top), +120 deg (bottom right), +120 deg (bottom left)

    p0 = current_shape.points[0]
    # Expected top point: 100 + 50*cos(-90), 100 + 50*sin(-90) => 100, 50
    assert math.isclose(p0[0], 100, abs_tol=1e-5)
    assert math.isclose(p0[1], 50, abs_tol=1e-5)

    tool.on_up(150, 150, e)
    assert canvas.current_drawing_shape is None


def test_polygon_tool_draw_star():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.selected_polygon_type = "star"

    canvas = BlackboardCanvas(app_state)
    tool = PolygonTool(canvas)

    e = MagicMock()
    tool.on_down(100, 100, e)
    tool.on_move(150, 150, e)

    shape = canvas.current_drawing_shape
    assert shape.polygon_type == "star"
    # Star has 5 points * 2 (inner and outer) = 10 points
    assert len(shape.points) == 10


def test_polygon_tool_shift_modifier():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.selected_polygon_type = "triangle"
    app_state.is_shift_down = True

    canvas = BlackboardCanvas(app_state)
    tool = PolygonTool(canvas)

    e = MagicMock()
    tool.on_down(100, 100, e)

    # Drag non-uniformly: 100,100 -> 200, 120 (dx=100, dy=20)
    # With shift, radius should be max(100, 20) = 100 for both
    tool.on_move(200, 120, e)

    shape = canvas.current_drawing_shape
    p0 = shape.points[0]
    # Expected top point: 100 + 100*cos(-90), 100 + 100*sin(-90) => 100, 0
    # If it wasn't constrained, it would be 100 + 100*cos(-90), 100 + 20*sin(-90) => 100, 80

    assert math.isclose(p0[1], 0, abs_tol=1e-5)


def test_polygon_tool_types_coverage():
    # Loop through other types to ensure generation code runs
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = PolygonTool(canvas)
    e = MagicMock()

    types = ["diamond", "pentagon", "hexagon", "octagon", "unknown"]
    expected_sides = [4, 5, 6, 8, 3]  # unknown defaults to 3

    for i, p_type in enumerate(types):
        app_state.selected_polygon_type = p_type
        tool.on_down(100, 100, e)
        tool.on_move(110, 110, e)
        shape = canvas.current_drawing_shape
        assert len(shape.points) == expected_sides[i]
        tool.on_up(110, 110, e)


def test_polygon_tool_no_shape_on_move():
    # Safety check if move called without shape
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = PolygonTool(canvas)

    canvas.current_drawing_shape = None
    e = MagicMock()
    # Should not raise
    tool.on_move(100, 100, e)


def test_polygon_tool_wrong_shape_on_move():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = PolygonTool(canvas)

    # Simulate some other shape active
    from blackboard.models import Rectangle

    # Create a rectangle (width/height 10)
    rect = Rectangle(x=10, y=10, width=10, height=10)
    canvas.current_drawing_shape = rect

    e = MagicMock()
    tool.on_move(100, 100, e)
    # Points shouldn't change / no error
    assert canvas.current_drawing_shape.width == 10
