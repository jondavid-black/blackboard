from blackboard.state.app_state import AppState
from blackboard.models import Rectangle, Line
from conftest import MockStorageService


def test_line_follows_anchor_on_resize():
    """
    Verify that if a Line is connected to a specific anchor of a Shape,
    resizing the Shape updates the Line's endpoint to the new anchor position.
    """
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)

    # 1. Create a rectangle
    # 0,0 100x100.
    # Anchors: top_left (0,0), top_right (100,0), bottom_right (100,100), etc.
    rect = Rectangle(x=0, y=0, width=100, height=100)
    app_state.add_shape(rect)

    # 2. Create a line connected to "bottom_right" anchor
    # Anchor should be at 100, 100
    line = Line(
        x=200,
        y=200,  # Start somewhere else
        end_x=100,
        end_y=100,  # Connected to bottom_right
        start_shape_id=None,
        end_shape_id=rect.id,
        end_anchor_id="bottom_right",
    )
    app_state.add_shape(line)

    # 3. Resize the rectangle
    # Simulate what Canvas does: modify properties directly
    # Let's resize it to 200x200
    rect.width = 200
    rect.height = 200

    # "bottom_right" should now be at (200, 200)

    # 4. Trigger the update mechanism
    # Currently Canvas calls notify(), but we want to introduce a method for this.
    # Let's assume we use app_state.update_shape(rect)
    app_state.update_shape(rect)

    # 5. Verify line end moved
    assert line.end_x == 200
    assert line.end_y == 200
