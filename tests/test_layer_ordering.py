import pytest
from blackboard.state.app_state import AppState
from blackboard.models import Rectangle


@pytest.fixture
def app_state():
    state = AppState(
        storage_service=None
    )  # Mock storage not strictly needed if we don't save
    # Create some shapes
    s1 = Rectangle(id="1", type="rectangle", x=0, y=0, width=10, height=10)
    s2 = Rectangle(id="2", type="rectangle", x=10, y=10, width=10, height=10)
    s3 = Rectangle(id="3", type="rectangle", x=20, y=20, width=10, height=10)
    s4 = Rectangle(id="4", type="rectangle", x=30, y=30, width=10, height=10)
    state.shapes = [s1, s2, s3, s4]
    return state


def test_move_to_front(app_state):
    # s1 is at index 0 (bottom), s4 is at index 3 (top)

    # Move s1 to front (end of list)
    app_state.move_shape_to_front("1")
    assert [s.id for s in app_state.shapes] == ["2", "3", "4", "1"]

    # Move s3 (now at index 1) to front
    app_state.move_shape_to_front("3")
    assert [s.id for s in app_state.shapes] == ["2", "4", "1", "3"]


def test_move_to_back(app_state):
    # s1 is at index 0 (bottom), s4 is at index 3 (top)

    # Move s4 to back (start of list)
    app_state.move_shape_to_back("4")
    assert [s.id for s in app_state.shapes] == ["4", "1", "2", "3"]

    # Move s2 (now at index 2) to back
    app_state.move_shape_to_back("2")
    assert [s.id for s in app_state.shapes] == ["2", "4", "1", "3"]


def test_reorder_shape(app_state):
    # Initial: ["1", "2", "3", "4"]

    # Move "1" to position of "3"
    # Logic: pop "1", insert at index of "3".
    # Index of "3" is 2.
    # After pop("1"), list is ["2", "3", "4"]. Index 2 is "4".
    # Wait, if we use current index of target "3" which is 2.
    # Result should be ["2", "1", "3", "4"] or ["2", "3", "1", "4"]?
    # Usually drag and drop on top of an item puts it *before* or *at that position*.

    # Let's see implementation:
    # pop source
    # insert at target_idx
    # if source_idx < target_idx: target_idx -= 1

    # Case 1: Move forward (down in list logic, up in visual Z-index)
    # Move "1" (idx 0) to "3" (idx 2)
    # source=0, target=2
    # pop "1" -> ["2", "3", "4"]
    # source < target, so target_idx becomes 1 (index of "3")
    # New Logic: insert "1" at target_idx + 1 = 2 -> ["2", "3", "1", "4"]
    app_state.reorder_shape("1", "3")
    assert [s.id for s in app_state.shapes] == ["2", "3", "1", "4"]

    # Reset
    app_state.shapes.sort(key=lambda s: s.id)  # 1, 2, 3, 4

    # Case 2: Move backward
    # Move "4" (idx 3) to "2" (idx 1)
    # source=3, target=1
    # pop "4" -> ["1", "2", "3"]
    # source > target, target_idx stays 1 (index of "2")
    # New Logic: insert "4" at target_idx + 1 = 2 -> ["1", "2", "4", "3"]
    app_state.reorder_shape("4", "2")
    assert [s.id for s in app_state.shapes] == ["1", "2", "4", "3"]
