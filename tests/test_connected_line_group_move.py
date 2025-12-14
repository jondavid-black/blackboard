from blackboard.state.app_state import AppState
from blackboard.models import Rectangle, Line
from blackboard.ui.canvas import BlackboardCanvas
from conftest import MockStorageService


def test_move_group_with_connected_line_and_anchor():
    """
    Test that when moving a group containing a shape and a connected line,
    the line's connection point remains anchored to the shape if the line is NOT selected
    (implicit movement via anchor) OR if the line IS selected (explicit movement).

    Wait, the requirement is: "non-connector lines but leave the connector lines attached to the object connector points"
    This implies:
    1. If I move a Rectangle.
    2. And there is a Line connected to it.
    3. The Line is NOT selected.
    4. The Line end connected to the Rectangle should move WITH the Rectangle (stay attached).
    5. The other end of the Line (if not connected to a moving object) should stay put.

    BUT, the user says: "If there are connections between objects the connection points on the connector lines should not move, they should remain attached to the connection point just as when moving a single object."

    This phrasing is slightly ambiguous. "should not move" usually means "stay relative to the object".
    "remain attached" means the coordinate updates to match the object's new position.

    Scenario A: Move ONLY the Rectangle. The connected line end MUST move to follow it.
    Scenario B: Move BOTH Rectangle and Line. Both move. Relative connection is preserved.

    The user bug report says: "If I drag one of the selected objects all selected objects should move." -> We fixed this.
    "But this introduced a bug... just move the objects and non-connector lines but leave the connector lines attached to the object connector points."

    If I select ONLY the Rectangle and move it, the line end attached to it should update.
    This is standard "connected line" behavior.

    If I select BOTH Rectangle and Line and move them, they both move by dx, dy. The connection is naturally preserved because both endpoints shift equally.

    So what is the bug?
    Maybe the `update_shape_position` logic is *double applying* the move?
    Or maybe it's NOT updating the line when the line is NOT selected?

    Let's look at `update_shape_position` in `app_state.py`.

    ```python
    def update_shape_position(self, shape, dx, dy, save=True):
        # Update shape...
        shape.x += dx
        shape.y += dy
        # ...
        # Update connected lines
        self._update_connected_lines(shape, dx, dy)
    ```

    `_update_connected_lines` finds lines connected to `shape` and adds `dx`, `dy` to the connected endpoint.

    If the Line is ALSO selected, `update_shape_position` will be called for the Line as well (because we iterate over all selected shapes in `canvas.py`).

    So:
    1. Loop selected shapes.
    2. Found Rectangle -> `update_shape_position(Rect, dx, dy)`
       -> Moves Rect.
       -> `_update_connected_lines` moves Line end (attached to Rect) by dx, dy.
    3. Found Line -> `update_shape_position(Line, dx, dy)`
       -> Moves Line (x, y, end_x, end_y) by dx, dy.

    Result: The attached end of the Line gets moved TWICE. Once by the Rect's update, and once by the Line's own update.
    This causes the line to "detach" or move faster than the object.

    We need to prevent this double movement.
    """
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)

    # 1. Setup
    # Rectangle at 100,100
    rect = Rectangle(id="rect1", x=100, y=100, width=100, height=100)
    app_state.add_shape(rect)

    # Line connected to Rect (start at 150,150 center of rect? or anchored)
    # Let's say anchored at "top_left" (100,100)
    line = Line(
        id="line1",
        x=100,
        y=100,
        end_x=50,
        end_y=50,
        start_shape_id="rect1",
        start_anchor_id="top_left",
    )
    app_state.add_shape(line)

    # 2. Select BOTH
    app_state.select_shapes(["rect1", "line1"])

    # 3. Move
    canvas = BlackboardCanvas(app_state)
    canvas.update = lambda: None

    # Simulate move of 10, 10
    # In `on_pan_update` or `update_active_interaction`:
    # It calls `app_state.update_shape_position(shape, dx, dy)` for EACH selected shape.

    dx, dy = 10, 10

    # Manually mimic the loop in canvas.py to verify the logic flaw in isolation first
    # Or just use the app_state method directly if we want to test that level.
    # The loop is:
    # for shape in app_state.shapes:
    #    if shape.id in selected_ids:
    #        app_state.update_shape_position(shape, dx, dy)

    # Move Rect
    app_state.update_shape_position(rect, dx, dy)
    # Move Line
    app_state.update_shape_position(line, dx, dy)

    # 4. Verify
    # Rect should be at 110, 110
    assert rect.x == 110
    assert rect.y == 110

    # Line start (attached to Rect) should be at 110, 110
    # If double moved, it would be 120, 120
    assert line.x == 110, f"Line start x should be 110, but is {line.x}"
    assert line.y == 110, f"Line start y should be 110, but is {line.y}"

    # Line end (not attached) should be at 60, 60 (moved once)
    assert line.end_x == 60
    assert line.end_y == 60
