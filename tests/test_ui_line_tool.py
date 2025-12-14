from unittest.mock import MagicMock
import math
import flet as ft
from blackboard.state.app_state import AppState
from blackboard.models import Line, Rectangle
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.ui.tools.line_tool import LineTool
from conftest import MockStorageService


def test_line_tool_init():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = LineTool(canvas)
    assert tool.app_state == app_state


def test_line_tool_draw_simple_line():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    # Ensure light mode for predictable color
    app_state.theme_mode = "light"
    canvas = BlackboardCanvas(app_state)
    tool = LineTool(canvas)
    e = MagicMock()

    # Down
    tool.on_down(100, 100, e)
    current_shape = canvas.current_drawing_shape
    assert isinstance(current_shape, Line)
    assert current_shape.x == 100
    assert current_shape.y == 100
    assert current_shape.end_x == 100
    assert current_shape.end_y == 100
    assert current_shape.stroke_color == ft.Colors.BLACK
    assert current_shape in app_state.shapes

    # Move
    tool.on_move(200, 200, e)
    assert current_shape.end_x == 200
    assert current_shape.end_y == 200

    # Up
    tool.on_up(200, 200, e)
    assert canvas.current_drawing_shape is None
    # Shape should still be in app_state
    assert current_shape in app_state.shapes


def test_line_tool_shift_snap():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = LineTool(canvas)
    e = MagicMock()

    # Start drawing
    tool.on_down(0, 0, e)

    # Simulate Shift key down
    app_state.is_shift_down = True

    # Move to a point that is clearly closer to 45 degrees (e.g. 100, 90)
    # 45 degrees would be (100, 100).
    tool.on_move(100, 90, e)

    current_shape = canvas.current_drawing_shape
    # Should snap to (100, 100) approx (length preservation logic might vary)
    # The code calculates length and angle.
    # dx=100, dy=90. Length = sqrt(100^2 + 90^2) = 134.53
    # Angle = atan2(90, 100) = 0.73 rad (~42 deg)
    # Snap angle should be pi/4 (45 deg) = 0.785 rad
    # New end_x = 0 + 134.53 * cos(pi/4) = 134.53 * 0.707 = 95.1
    # New end_y = 0 + 134.53 * sin(pi/4) = 95.1

    expected_length = math.sqrt(100**2 + 90**2)
    expected_x = expected_length * math.cos(math.pi / 4)
    expected_y = expected_length * math.sin(math.pi / 4)

    assert math.isclose(current_shape.end_x, expected_x, rel_tol=1e-5)
    assert math.isclose(current_shape.end_y, expected_y, rel_tol=1e-5)


def test_line_tool_snap_to_shape_start():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = LineTool(canvas)
    e = MagicMock()

    # Create a rectangle to snap to
    rect = Rectangle(x=50, y=50, width=100, height=100)
    rect.id = "rect1"
    app_state.add_shape(rect)

    # Mock hit_test to return the rectangle
    canvas.hit_test = MagicMock(return_value=rect)

    # Start drawing on top of rectangle
    tool.on_down(60, 60, e)

    current_shape = canvas.current_drawing_shape
    assert current_shape.start_shape_id == "rect1"


def test_line_tool_snap_to_anchor_start():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = LineTool(canvas)
    e = MagicMock()

    # Create a rectangle
    rect = Rectangle(x=0, y=0, width=100, height=100)
    rect.id = "rect1"
    app_state.add_shape(rect)

    # Mock hit_test and get_anchors
    canvas.hit_test = MagicMock(return_value=rect)
    # Mock anchor at (50, 0) - top center
    canvas.get_anchors = MagicMock(return_value=[("top", 50, 0)])

    # Start drawing close to anchor
    # Default zoom is 1.0, threshold is 10
    tool.on_down(55, 5, e)

    current_shape = canvas.current_drawing_shape
    assert current_shape.start_shape_id == "rect1"
    assert current_shape.start_anchor_id == "top"
    # Should have snapped coordinates to (50, 0)
    assert current_shape.x == 50
    assert current_shape.y == 0


def test_line_tool_snap_to_anchor_end():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = LineTool(canvas)
    e = MagicMock()

    # Create a rectangle to snap end to
    rect = Rectangle(x=200, y=0, width=100, height=100)
    rect.id = "rect1"
    app_state.add_shape(rect)

    # Start drawing away from rect
    canvas.hit_test = MagicMock(return_value=None)
    tool.on_down(0, 0, e)

    # Setup for on_up snap logic
    # on_up iterates app_state.shapes
    canvas.get_anchors = MagicMock(return_value=[("left", 200, 50)])

    # End drawing close to the rectangle's left anchor
    tool.on_up(195, 52, e)

    # Get the line that was just finished (it's no longer current_drawing_shape)
    # It should be the last shape added
    line = app_state.shapes[-1]
    assert isinstance(line, Line)

    assert line.end_shape_id == "rect1"
    assert line.end_anchor_id == "left"
    assert line.end_x == 200
    assert line.end_y == 50


def test_line_tool_draw_overlays():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = LineTool(canvas)

    overlay_shapes = []

    # Mock hover state
    canvas.hover_wx = 100
    canvas.hover_wy = 100

    # 1. Hovering over a shape
    rect = Rectangle(x=50, y=50, width=100, height=100)
    rect.id = "rect1"
    app_state.add_shape(rect)

    canvas.hit_test = MagicMock(return_value=rect)
    canvas.get_anchors = MagicMock(return_value=[("center", 100, 100)])
    canvas.to_screen = MagicMock(side_effect=lambda x, y: (x, y))  # Identity transform

    tool.draw_overlays(overlay_shapes)

    # Should have added a circle for the anchor
    assert len(overlay_shapes) == 1
    circle = overlay_shapes[0]
    assert isinstance(circle, ft.canvas.Circle)
    assert circle.x == 100
    assert circle.y == 100


def test_line_tool_draw_overlays_dragging_snap():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = LineTool(canvas)

    overlay_shapes = []

    # Setup active drawing line
    line = Line(x=0, y=0, end_x=10, end_y=10)
    line.id = "line1"
    canvas.current_drawing_shape = line
    app_state.add_shape(line)

    # Setup target shape for snapping
    rect = Rectangle(x=100, y=100, width=50, height=50)
    rect.id = "rect1"
    app_state.add_shape(rect)

    # Mock current mouse position close to anchor
    canvas.last_wx = 105
    canvas.last_wy = 105

    canvas.hit_test = MagicMock(return_value=None)  # Not hovering start
    canvas.get_anchors = MagicMock(return_value=[("corner", 100, 100)])
    canvas.to_screen = MagicMock(side_effect=lambda x, y: (x, y))

    tool.draw_overlays(overlay_shapes)

    # Should see snap highlight (green circle) + anchor points
    # Logic:
    # 1. Snap highlight circle
    # 2. Context anchors for the target shape

    # We expect at least the snap circle
    assert len(overlay_shapes) >= 1

    # Check for green snap circle
    snap_circle = next(
        (
            s
            for s in overlay_shapes
            if isinstance(s, ft.canvas.Circle) and s.radius == 8
        ),
        None,
    )
    assert snap_circle is not None
    assert snap_circle.paint.color == ft.Colors.GREEN
