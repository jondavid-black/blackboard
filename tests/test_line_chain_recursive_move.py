from blackboard.models import Line
from blackboard.state.app_state import AppState
from conftest import MockStorageService


def test_chained_line_connection_move_recursive():
    """
    Test that moving a connector line (Line B) that is connected to Line A
    correctly updates Line C which is connected to Line B.

    Structure: Line A -> Line B (start attached to A end) -> Line C (start attached to B end)
    Action: Move Line B.
    Expectation:
        - Line B moves.
        - Line A end follows Line B start (if attached to it? No, Line B is attached TO Line A).
          If Line B moves, and it is attached to Line A, strictly speaking, it should DETACH if dragged away?
          Or, if we move Line B, we are effectively moving the "child". The parent (Line A) stays put?
          In `update_shape_position`, we update connected lines.
          `_update_connected_lines` updates lines that are connected TO the moved shape.

          If Line B is moved:
          - Line C (start attached to B end) should move its start point.
          - Line A? Line B is attached TO Line A. Line A is not attached TO Line B.
            So Line A should not move.
            BUT, does Line B stay attached to Line A?
            If we drag Line B, we are changing its x/y.
            The `update_shape_position` updates x/y.
            If Line B is defined as "attached to A", usually dragging it might detach it?
            Or it just moves and the connection data remains but visually it separates?

            Current logic: `update_shape_position` just updates x/y. It does NOT check if `start_shape_id` is set.
            It does NOT clear `start_shape_id` on move.
            So it stays "logically" connected but visually disconnected.

            UNLESS:
            When we move a shape, we should check if IT is connected to something?
            The prompt says: "When the lines move ensure the connector points remain attached."

            This implies that if I move Line B, and it is attached to Line A,
            Line B's start point should STAY at Line A's anchor (effectively resizing Line B)?
            OR Line A's anchor point should move (modifying Line A)?

            Usually in diagramming tools:
            - If I select a connector line and drag it, I am moving the whole line.
              If it was attached, it usually detaches.
            - OR, if I drag the *endpoint* handle, I can move just that end.

            BUT, if the user implies "When the lines move ensure the connector points remain attached",
            maybe they mean:
            1. If I move a Shape (Rect), the attached Line moves its end to stay attached. (This works).
            2. If I move a Connector Line (Line B), and it has another Line (Line C) attached to it, Line C should update. (This works).
            3. If I move a Connector Line (Line B), and Line B is attached to Line A...
               Should Line B detach? Or should it stretch?
               If I select the whole line B and drag, usually it detaches.

            Let's re-read the prompt: "There is a bug in the movement of connected connector lines. When the lines move ensure the connector points remain attached."

            This might refer to the case where we move a group of connected lines?
            Or maybe the recursive update isn't working for Line-to-Line?

            Let's repro the "Line C attached to Line B" case first.
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

    # Line C: Connected to Line B's end
    line_c = Line(
        id="line_c",
        x=100,
        y=100,
        end_x=200,
        end_y=100,
        start_shape_id="line_b",
        start_anchor_id="end",
    )
    app_state.add_shape(line_c)

    # Move Line A.
    # Line B should update its start.
    # Line B's end stays put?
    # Wait, if Line B start moves, does Line B end move?
    # In `_update_connected_lines`:
    # if s.start_shape_id == moved_shape.id:
    #    s.x += dx; s.y += dy
    # This MOVES the start point. It does NOT change end point.
    # So Line B stretches.
    # Line B's END point (at 100, 100) does NOT change.
    # Therefore Line C (attached to Line B end) should NOT change.

    app_state.update_shape_position(line_a, 50, 0)

    # Line A moved
    assert line_a.x == 50
    assert line_a.end_x == 150  # moved 50

    # Line B start should move 50
    assert line_b.x == 150
    # Line B end should stay at 100?
    # The current implementation of `_update_connected_lines` for `start_shape_id` match is:
    # s.x += dx, s.y += dy.
    # It does NOT touch end_x, end_y.
    assert line_b.end_x == 100

    # Line C start should stay at 100?
    assert line_c.x == 100

    # Now, what if we move Line B?
    # We move Line B by (10, 10).
    app_state.update_shape_position(line_b, 10, 10)

    # Line B moves
    assert line_b.x == 160
    assert line_b.end_x == 110

    # Line C attached to Line B end.
    # Line C start should move by (10, 10).
    assert line_c.x == 110
    assert line_c.y == 110
