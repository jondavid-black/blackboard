from whiteboard.state.app_state import AppState
from whiteboard.models import ToolType, Line


class MockListener:
    def __init__(self):
        self.call_count = 0

    def __call__(self):
        self.call_count += 1


def test_initial_state():
    state = AppState()
    assert state.shapes == []
    assert state.selected_shape_id is None
    assert state.current_tool == ToolType.HAND
    assert state.pan_x == 0.0
    assert state.pan_y == 0.0
    assert state.zoom == 1.0


def test_set_tool():
    state = AppState()
    listener = MockListener()
    state.add_listener(listener)

    state.set_tool(ToolType.LINE)
    assert state.current_tool == ToolType.LINE
    assert listener.call_count == 1


def test_add_shape():
    state = AppState()
    listener = MockListener()
    state.add_listener(listener)

    line = Line(x=10, y=10, end_x=20, end_y=20)
    state.add_shape(line)

    assert len(state.shapes) == 1
    assert state.shapes[0] == line
    assert listener.call_count == 1


def test_select_shape():
    state = AppState()
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
    state = AppState()
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
    state = AppState()
    state.set_pan(100.0, 200.0)
    assert state.pan_x == 100.0
    assert state.pan_y == 200.0


def test_listener_management():
    state = AppState()
    listener = MockListener()

    state.add_listener(listener)
    state.notify()
    assert listener.call_count == 1

    state.remove_listener(listener)
    state.notify()
    assert listener.call_count == 1
