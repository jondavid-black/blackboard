import pytest
from blackboard.state.app_state import AppState
from blackboard.models import Rectangle, Line
from blackboard.storage.storage_service import StorageService


class MockStorageService(StorageService):
    def __init__(self):
        self.current_file = "test.json"

    def load_data(self):
        return [], {"pan_x": 0.0, "pan_y": 0.0, "zoom": 1.0}

    def save_data(self, shapes, pan_x, pan_y, zoom, immediate=False):
        pass

    def _serialize_shape(self, shape):
        import dataclasses

        return dataclasses.asdict(shape)

    def _deserialize_shape(self, data):
        return super()._deserialize_shape(data)


@pytest.fixture
def clean_state():
    return AppState(storage_service=MockStorageService())


def test_copy_paste(clean_state):
    state = clean_state

    # 1. Create and select a rectangle
    rect = Rectangle(x=10, y=10, width=50, height=50)
    state.add_shape(rect)
    state.select_shape(rect.id)

    # 2. Copy
    state.copy()
    assert len(state.clipboard) == 1
    assert state.clipboard[0]["type"] == "rectangle"

    # 3. Paste
    state.paste()

    # Should have 2 shapes now
    assert len(state.shapes) == 2

    # The new shape should be offset
    original = state.shapes[0]
    pasted = state.shapes[1]

    assert pasted.x == original.x + 20
    assert pasted.y == original.y + 20
    assert pasted.id != original.id

    # Pasted shape should be selected
    assert len(state.selected_shape_ids) == 1
    assert pasted.id in state.selected_shape_ids


def test_copy_paste_line(clean_state):
    state = clean_state

    line = Line(x=0, y=0, end_x=100, end_y=100)
    state.add_shape(line)
    state.select_shape(line.id)

    state.copy()
    state.paste()

    pasted = state.shapes[1]
    assert pasted.x == 20
    assert pasted.y == 20
    assert pasted.end_x == 120
    assert pasted.end_y == 120


def test_undo_paste(clean_state):
    state = clean_state
    rect = Rectangle(x=10, y=10)
    state.add_shape(rect)
    state.select_shape(rect.id)
    state.copy()

    # Paste
    state.paste()
    assert len(state.shapes) == 2

    # Undo Paste
    state.undo()
    assert len(state.shapes) == 1
    assert state.shapes[0].id == rect.id
