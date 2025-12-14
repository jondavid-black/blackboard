from blackboard.state.app_state import AppState
from blackboard.models import Line
from conftest import MockStorageService


def test_line_connects_to_line_endpoints():
    """
    Verify that a Line can connect to another Line's endpoints,
    and updates when the target Line is moved or resized.
    """
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)

    # 1. Create Line A
    line_a = Line(x=0, y=0, end_x=100, end_y=0)
    app_state.add_shape(line_a)

    # 2. Create Line B connected to Line A's end
    # Simulating the connection creation
    line_b = Line(
        x=100,
        y=0,
        end_x=100,
        end_y=100,
        start_shape_id=line_a.id,
        start_anchor_id="end",
    )
    app_state.add_shape(line_b)

    # 3. Move Line A
    # app_state.update_shape_position handles translation
    app_state.update_shape_position(line_a, 50, 50)

    # Line A should be at (50, 50) -> (150, 50)
    assert line_a.x == 50
    assert line_a.y == 50
    assert line_a.end_x == 150
    assert line_a.end_y == 50

    # Line B start should follow Line A's end (150, 50)
    assert line_b.x == 150
    assert line_b.y == 50
    # Line B end should move too? NO.
    # update_shape_position updates connected lines endpoints.
    # In `_update_connected_lines`:
    # if s.start_shape_id == moved_shape.id: s.x += dx; s.y += dy
    # It TRANSLATES the endpoint. It does NOT strictly set it to the anchor position unless we call `_refresh_connected_lines`.
    # But `update_shape_position` applies `dx, dy` recursively.
    # So Line B start moved by (50, 50).
    # Line B end is NOT connected to anything, so it stays?
    # Wait, `_update_connected_lines` implementation:
    # if start connected: s.x += dx, s.y += dy.
    # It does NOT move s.end_x/end_y unless the END is also connected.
    # So Line B stretches?
    # Yes, typically if you move the object attached to one end, the line stretches.

    assert line_b.end_x == 100
    assert line_b.end_y == 100

    # 4. Resize Line A
    # Move Line A's end point further to (200, 50)
    # This simulates dragging the handle.
    # We update the shape directly and call update_shape (which calls _refresh_connected_lines)
    line_a.end_x = 200
    line_a.end_y = 50
    app_state.update_shape(line_a)

    # Line B start should snap to new Line A end (200, 50)
    # because it is anchored to "end".
    assert line_b.x == 200
    assert line_b.y == 50
