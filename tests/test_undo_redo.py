import pytest
from blackboard.state.app_state import AppState
from blackboard.models import Rectangle, Circle
from blackboard.storage.storage_service import StorageService


# Mock storage to avoid reading from disk during tests
class MockStorageService(StorageService):
    def __init__(self):
        self.current_file = "test.json"

    def load_data(self):
        return [], {"pan_x": 0.0, "pan_y": 0.0, "zoom": 1.0}

    def save_data(self, shapes, pan_x, pan_y, zoom, immediate=False):
        pass

    def _serialize_shape(self, shape):
        # We need this for the undo stack deep copy mechanism
        # Reuse parent implementation or simple dict
        import dataclasses

        return dataclasses.asdict(shape)

    def _deserialize_shape(self, data):
        # Reuse parent logic which handles types
        return super()._deserialize_shape(data)


@pytest.fixture
def clean_state():
    # Use mock storage so we start with empty state
    return AppState(storage_service=MockStorageService())


def test_undo_stack_grows_on_add(clean_state):
    state = clean_state

    rect = Rectangle(x=10, y=10, width=50, height=50)
    state.add_shape(rect)

    assert len(state.shapes) == 1
    assert len(state.undo_stack) == 1
    # Undo stack should contain empty list (state before add)
    assert len(state.undo_stack[0]) == 0


def test_undo_add(clean_state):
    state = clean_state
    rect = Rectangle(x=10, y=10, width=50, height=50)
    state.add_shape(rect)

    state.undo()

    assert len(state.shapes) == 0
    assert len(state.undo_stack) == 0
    assert len(state.redo_stack) == 1


def test_redo_add(clean_state):
    state = clean_state
    rect = Rectangle(x=10, y=10, width=50, height=50)
    state.add_shape(rect)
    state.undo()
    state.redo()

    assert len(state.shapes) == 1
    assert state.shapes[0].type == "rectangle"
    assert len(state.undo_stack) == 1
    assert len(state.redo_stack) == 0


def test_multiple_undo_redo(clean_state):
    state = clean_state

    # Step 1: Add Rect
    rect = Rectangle(x=10, y=10)
    state.add_shape(rect)  # Stack: [[]]

    # Step 2: Add Circle
    circle = Circle(x=100, y=100)
    state.add_shape(circle)  # Stack: [[], [Rect]]

    assert len(state.shapes) == 2
    assert len(state.undo_stack) == 2

    # Undo Circle
    state.undo()
    assert len(state.shapes) == 1
    assert isinstance(state.shapes[0], Rectangle)

    # Undo Rect
    state.undo()
    assert len(state.shapes) == 0

    # Redo Rect
    state.redo()
    assert len(state.shapes) == 1
    assert isinstance(state.shapes[0], Rectangle)

    # Redo Circle
    state.redo()
    assert len(state.shapes) == 2
    assert isinstance(state.shapes[1], Circle)


def test_snapshot_limit(clean_state):
    state = clean_state

    # Simulate 60 actions
    for i in range(60):
        state.add_shape(Rectangle(x=i, y=i))

    # Stack should be capped at 50
    assert len(state.undo_stack) == 50

    state.undo()
    assert len(state.shapes) == 59
