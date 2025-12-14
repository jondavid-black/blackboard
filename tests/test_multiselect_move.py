from blackboard.models import Line
from blackboard.state.app_state import AppState
from blackboard.storage.storage_service import StorageService


class MockStorageService(StorageService):
    def load_data(self):
        return [], {}

    def save_data(self, shapes, pan_x, pan_y, zoom, immediate=False):
        pass


def test_multiselect_move_preserves_connection():
    """
    Test that moving two selected lines (where one is connected to the other)
    does not result in double movement or broken connections.

    Structure: Line A (0,0 -> 100,0) -> Line B (attached to A's end)
    Selection: Both A and B.
    Action: Move both by (10, 10).
    Expectation:
        - Line A moves to (10, 10 -> 110, 10).
        - Line B moves to (110, 10 -> 110, 110).
        - Connection remains valid (B start == A end).
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

    # Select both
    app_state.select_shapes(["line_a", "line_b"])

    # Simulate movement
    # In a real UI, if multiple items are selected, the tool iterates and updates each.
    # We must simulate that behavior here.
    dx = 10
    dy = 10

    # Order matters? It shouldn't, but let's try A then B (standard list order)
    # The app usually iterates through `selected_shape_ids`.

    # Move A
    app_state.update_shape_position(line_a, dx, dy)
    # Move B
    app_state.update_shape_position(line_b, dx, dy)

    # Check Final Positions

    # Line A should have moved ONCE: 0,0 -> 10,10
    assert line_a.x == 10
    assert line_a.y == 10
    assert line_a.end_x == 110
    assert line_a.end_y == 10

    # Line B should have moved ONCE: 100,0 -> 110,10
    assert line_b.x == 110
    assert line_b.y == 10

    # Verify connection
    assert line_b.x == line_a.end_x
    assert line_b.y == line_a.end_y
