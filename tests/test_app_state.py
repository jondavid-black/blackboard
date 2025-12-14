from blackboard.state.app_state import AppState
from blackboard.models import ToolType, Line
from conftest import MockStorageService


class MockListener:
    def __init__(self):
        self.call_count = 0

    def __call__(self):
        self.call_count += 1


def test_initial_state():
    storage = MockStorageService()
    state = AppState(storage_service=storage)
    assert state.shapes == []
    assert state.selected_shape_id is None
    assert state.current_tool == ToolType.HAND
    assert state.pan_x == 0.0
    assert state.pan_y == 0.0
    assert state.zoom == 1.0


def test_set_tool():
    storage = MockStorageService()
    state = AppState(storage_service=storage)
    listener = MockListener()
    state.add_listener(listener)

    state.set_tool(ToolType.LINE)
    assert state.current_tool == ToolType.LINE
    assert listener.call_count == 1


def test_add_shape():
    storage = MockStorageService()
    state = AppState(storage_service=storage)
    listener = MockListener()
    state.add_listener(listener)

    line = Line(x=10, y=10, end_x=20, end_y=20)
    state.add_shape(line)

    assert len(state.shapes) == 1
    assert state.shapes[0] == line
    assert listener.call_count == 1


def test_select_shape():
    storage = MockStorageService()
    state = AppState(storage_service=storage)
    listener = MockListener()
    state.add_listener(listener)

    line = Line()
    state.add_shape(line)

    state.select_shape(line.id)
    assert state.selected_shape_id == line.id
    assert listener.call_count == 2  # 1 for add, 1 for select

    state.select_shape(None)
    assert state.selected_shape_id is None
    assert listener.call_count == 3


def test_tool_change_clears_selection():
    storage = MockStorageService()
    state = AppState(storage_service=storage)
    line = Line()
    state.add_shape(line)
    state.select_shape(line.id)

    # Switching to drawing tool should clear selection
    state.set_tool(ToolType.RECTANGLE)
    assert state.selected_shape_id is None

    # Switching to HAND should NOT clear selection (based on implementation logic check)
    # Let's check implementation:
    # if tool != ToolType.SELECTION and tool != ToolType.HAND: self.selected_shape_id = None

    state.select_shape(line.id)
    state.set_tool(ToolType.HAND)
    assert state.selected_shape_id == line.id

    state.set_tool(ToolType.SELECTION)
    assert state.selected_shape_id == line.id


def test_set_pan():
    storage = MockStorageService()
    state = AppState(storage_service=storage)
    state.set_pan(100.0, 200.0)
    assert state.pan_x == 100.0
    assert state.pan_y == 200.0


def test_listener_management():
    storage = MockStorageService()
    state = AppState(storage_service=storage)
    listener = MockListener()

    state.add_listener(listener)
    state.notify()
    assert listener.call_count == 1

    state.remove_listener(listener)
    state.notify()
    assert listener.call_count == 1


def test_file_management():
    storage = MockStorageService()
    state = AppState(storage_service=storage)
    listener = MockListener()
    state.add_listener(listener)

    # Initial state
    assert state.get_current_filename() == "default.json"

    # Create new file
    state.create_file("test.json")
    assert state.get_current_filename() == "test.json"
    assert "test.json" in state.list_files()
    assert listener.call_count >= 1

    # Switch back
    state.switch_file("default.json")
    assert state.get_current_filename() == "default.json"

    # Delete file
    state.delete_file("test.json")
    assert "test.json" not in state.list_files()

    # Deleting current file should switch to default/remaining
    # First re-create it to test this case
    state.create_file("todelete.json")
    assert state.get_current_filename() == "todelete.json"
    state.delete_file("todelete.json")
    # Should revert to default or another available file
    assert state.get_current_filename() == "default.json"


def test_create_file_without_extension():
    """Test that creating a file without .json extension works and switches correctly"""
    storage = MockStorageService()
    state = AppState(storage_service=storage)

    # Create file without extension
    state.create_file("project_alpha")

    # Should automatically add extension
    assert state.get_current_filename() == "project_alpha.json"
    assert "project_alpha.json" in state.list_files()


def test_move_shape_forward_backward():
    storage = MockStorageService()
    state = AppState(storage_service=storage)

    shape1 = Line()
    shape2 = Line()
    shape3 = Line()

    state.add_shape(shape1)
    state.add_shape(shape2)
    state.add_shape(shape3)

    assert state.shapes == [shape1, shape2, shape3]

    # Move shape1 forward (up)
    state.move_shape_forward(shape1.id)
    assert state.shapes == [shape2, shape1, shape3]

    # Move shape1 forward again
    state.move_shape_forward(shape1.id)
    assert state.shapes == [shape2, shape3, shape1]

    # Move shape1 forward again (should do nothing as it's at the top)
    state.move_shape_forward(shape1.id)
    assert state.shapes == [shape2, shape3, shape1]

    # Move shape1 backward (down)
    state.move_shape_backward(shape1.id)
    assert state.shapes == [shape2, shape1, shape3]

    # Move shape1 backward again
    state.move_shape_backward(shape1.id)
    assert state.shapes == [shape1, shape2, shape3]

    # Move shape1 backward again (should do nothing as it's at the bottom)
    state.move_shape_backward(shape1.id)
    assert state.shapes == [shape1, shape2, shape3]
