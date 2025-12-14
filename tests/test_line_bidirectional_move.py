from blackboard.models import Line
from blackboard.state.app_state import AppState
from blackboard.storage.storage_service import StorageService


class MockStorageService(StorageService):
    def load_data(self):
        return [], {}

    def save_data(self, shapes, pan_x, pan_y, zoom, immediate=False):
        pass


def test_move_child_line_updates_parent_line_endpoint():
    """
    Test that moving a connector line (Line B) that is connected to Line A
    correctly updates Line A's endpoint to maintain the connection.

    Structure: Line A (0,0 -> 100,0) -> Line B (attached to A's end)
    Action: Move Line B by (50, 50).
    Expectation:
        - Line B moves (start becomes 150, 50).
        - Line A end moves to matches Line B start (150, 50).
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

    # Move Line B
    app_state.update_shape_position(line_b, 50, 50)

    # Check Line B Moved
    assert line_b.x == 150
    assert line_b.y == 50

    # Check Line A "Pulled"
    # Currently this fails (Line A stays at 100,0)
    assert line_a.end_x == 150
    assert line_a.end_y == 50
