from blackboard.models import Line, Shape, Rectangle, Circle, Polygon, Text
from blackboard.state.app_state import AppState
from blackboard.ui.canvas import BlackboardCanvas
from conftest import MockStorageService


def test_line_to_line_connection():
    # 1. Setup
    app_state = AppState(storage_service=MockStorageService())

    # Create Line A (the target line)
    line_a = Line(id="line_a", x=100, y=100, end_x=200, end_y=100, type="line")
    app_state.add_shape(line_a)

    # Create Line B (the connector line)
    # Start it at Line A's end point
    line_b = Line(
        id="line_b",
        x=200,
        y=100,
        end_x=200,
        end_y=200,
        type="line",
        start_shape_id="line_a",
        start_anchor_id="end",  # This is what we need to implement
    )
    app_state.add_shape(line_b)

    # 2. Select Line A and Move it
    app_state.select_shape("line_a")
    dx, dy = 50, 50
    app_state.update_shape_position(line_a, dx, dy)

    # 3. Verification
    # Line A should have moved
    assert line_a.x == 150
    assert line_a.y == 150
    assert line_a.end_x == 250
    assert line_a.end_y == 150

    # Line B start point should have followed Line A's end point
    # Because line_b.start_anchor_id is "end" (of line_a)
    assert line_b.x == 250
    assert line_b.y == 150

    # Line B end point should NOT have moved (it wasn't selected)
    assert line_b.end_x == 200
    assert line_b.end_y == 200


def test_line_to_line_start_connection():
    # 1. Setup
    app_state = AppState(storage_service=MockStorageService())

    # Create Line A (the target line)
    line_a = Line(id="line_a", x=100, y=100, end_x=200, end_y=100)
    app_state.add_shape(line_a)

    # Create Line B connecting to start of Line A
    line_b = Line(
        id="line_b",
        x=100,
        y=100,
        end_x=100,
        end_y=200,
        start_shape_id="line_a",
        start_anchor_id="start",
    )
    app_state.add_shape(line_b)

    # 2. Move Line A
    app_state.select_shape("line_a")
    app_state.update_shape_position(line_a, 20, 20)

    # 3. Verify
    assert line_b.x == 120
    assert line_b.y == 120


def test_line_to_line_resize_connection():
    # 1. Setup
    app_state = AppState(storage_service=MockStorageService())

    # Create Line A
    line_a = Line(id="line_a", x=100, y=100, end_x=200, end_y=100)
    app_state.add_shape(line_a)

    # Create Line B connected to Line A's end
    line_b = Line(
        id="line_b",
        x=200,
        y=100,
        end_x=200,
        end_y=200,
        start_shape_id="line_a",
        start_anchor_id="end",
    )
    app_state.add_shape(line_b)

    # 2. Resize Line A (move end point)
    # This usually happens via update_shape in the canvas
    line_a.end_x = 300
    line_a.end_y = 150
    app_state.update_shape(line_a)

    # 3. Verify Line B followed
    assert line_b.x == 300
    assert line_b.y == 150


from blackboard.models import Line
from blackboard.state.app_state import AppState


def test_chained_line_connection_resize_recursive():
    """
    Test that updates propagate through a chain of connections.
    Line A -> Line B (start attached to A end) -> Line C (start attached to B start)

    If Line A end moves, Line B start moves.
    Since Line B start moves, Line C start (attached to B start) should also move.
    """
    app_state = AppState(storage_service=MockStorageService())

    # Line A
    line_a = Line(id="line_a", x=0, y=0, end_x=100, end_y=0)
    app_state.add_shape(line_a)

    # Line B: Connected to Line A's end
    line_b = Line(
        id="line_b",
        x=100,
        y=0,
        end_x=100,
        end_y=100,
        start_shape_id="line_a",
        start_anchor_id="end",
    )
    app_state.add_shape(line_b)

    # Line C: Connected to Line B's START
    # Note: connecting to B's start means it should share the same point as A's end and B's start.
    line_c = Line(
        id="line_c",
        x=100,
        y=0,
        end_x=200,
        end_y=0,
        start_shape_id="line_b",
        start_anchor_id="start",
    )
    app_state.add_shape(line_c)

    # Move Line A's end point (resize)
    line_a.end_x = 150
    line_a.end_y = 50
    app_state.update_shape(line_a)

    # Verify
    # Line B start should follow Line A end
    assert line_b.x == 150
    assert line_b.y == 50

    # Line C start should follow Line B start
    assert line_c.x == 150
    assert line_c.y == 50
