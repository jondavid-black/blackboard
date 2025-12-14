from blackboard.state.app_state import AppState
from blackboard.models import Rectangle, Line, ToolType
from conftest import MockStorageService


def test_line_stays_connected_when_shape_moves():
    """
    Verify that if a Line is connected to a Shape, moving the Shape
    automatically updates the Line's endpoints.
    """
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)

    # 1. Create two rectangles
    rect1 = Rectangle(x=0, y=0, width=50, height=50)
    rect2 = Rectangle(x=200, y=0, width=50, height=50)
    app_state.add_shape(rect1)
    app_state.add_shape(rect2)

    # 2. Create a connector line between them
    # Manually setting ids to simulate a created connection
    line = Line(
        x=25,
        y=25,
        end_x=225,
        end_y=25,
        line_type="connector",
        start_shape_id=rect1.id,
        end_shape_id=rect2.id,
    )
    app_state.add_shape(line)

    # 3. Select Rect1 and move it
    app_state.set_tool(ToolType.SELECTION)
    app_state.select_shape(rect1.id)

    # Simulate move in Canvas logic (or manually updating state if we implement it in AppState)
    # The current move logic is in BlackboardCanvas.update_active_interaction
    # But ideally, AppState should handle the "cascade" if we update the shape via `update_shape`.
    # However, canvas does direct property modification then notify().

    # Let's mimic what Canvas does: modify property -> notify
    # rect1.x = 0
    # rect1.y = 100 # Move down by 100

    # Trigger the update logic (which we need to implement)
    # Since we don't have the canvas instance driving this here, we might need to put the logic
    # in AppState.update_shape OR AppState.notify?
    # Better: AppState.update_shape should check for dependencies.
    # But Canvas modifies objects directly and calls notify().

    # So we need a mechanism. Let's assume we will implement a helper `move_shape` in AppState
    # or relying on `notify()` to recalculate lines? Recalculating on every notify might be expensive.

    # Let's try to invoke the logic we INTEND to write.
    # We will likely add `app_state.move_shape(shape_id, dx, dy)` or similar,
    # OR we make the Canvas responsible for updating dependent lines.
    # Given the architecture, Canvas handles interaction.
    # Let's assume we implement `app_state.update_shape_position(shape, new_x, new_y)`

    # Use the new AppState method
    app_state.update_shape_position(rect1, 0, 100)

    # CHECK: Line start point should have moved to match Rect1's new center/relative pos
    # Original offset was (25, 25) which is center of (0,0,50,50).
    # New center is (25, 125).
    assert line.x == 25
    assert line.y == 125
