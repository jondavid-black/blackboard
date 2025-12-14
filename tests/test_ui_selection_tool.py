from unittest.mock import MagicMock
from blackboard.state.app_state import AppState
from blackboard.models import Line, Rectangle, Group, Text
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.ui.tools.selection_tool import SelectionTool
from conftest import MockStorageService


def test_selection_tool_initialization():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = SelectionTool(canvas)

    assert tool.canvas == canvas
    assert tool.drag_start_wx == 0
    assert tool.drag_start_wy == 0
    assert tool.resize_handle is None
    assert tool.resizing_shape is None
    assert tool.moving_shapes_initial_state == {}


def test_selection_tool_select_shape():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = SelectionTool(canvas)

    # Add a shape
    rect = Rectangle(x=10, y=10, width=50, height=50)
    app_state.add_shape(rect)

    # Mock hit test
    canvas.hit_test = MagicMock(return_value=rect)

    # Simulate on_down
    e = MagicMock()
    tool.on_down(20, 20, e)

    assert app_state.selected_shape_id == rect.id
    assert app_state.selected_shape_ids == {rect.id}
    assert rect.id in tool.moving_shapes_initial_state


def test_selection_tool_deselect():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = SelectionTool(canvas)

    # Add a shape
    rect = Rectangle(x=10, y=10, width=50, height=50)
    app_state.add_shape(rect)
    app_state.select_shape(rect.id)

    # Mock hit test returning None (background click)
    canvas.hit_test = MagicMock(return_value=None)

    # Simulate on_down
    e = MagicMock(local_x=200, local_y=200)
    tool.on_down(200, 200, e)

    assert app_state.selected_shape_id is None
    assert len(app_state.selected_shape_ids) == 0
    # Should trigger pan logic
    assert tool._is_panning is True


def test_selection_tool_move_shape():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = SelectionTool(canvas)

    rect = Rectangle(x=10, y=10, width=50, height=50)
    app_state.add_shape(rect)

    # Select shape
    canvas.hit_test = MagicMock(return_value=rect)
    e = MagicMock()
    tool.on_down(20, 20, e)

    # Move
    tool.on_move(30, 30, e)

    assert rect.x == 20  # 10 + (30-20)
    assert rect.y == 20  # 10 + (30-20)

    # End move
    tool.on_up(30, 30, e)
    assert tool.moving_shapes_initial_state == {}


def test_selection_tool_resize_rectangle():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = SelectionTool(canvas)

    rect = Rectangle(x=10, y=10, width=50, height=50)
    app_state.add_shape(rect)
    app_state.select_shape(rect.id)

    # Mock hit test
    canvas.hit_test = MagicMock(return_value=rect)

    # Simulate hitting bottom-right handle
    # BR handle is at (60, 60)
    e = MagicMock()
    tool.on_down(60, 60, e)

    assert tool.resize_handle == "br"
    assert tool.resizing_shape == rect

    # Drag to (70, 70) -> increase size by 10
    tool.on_move(70, 70, e)

    assert rect.width == 60
    assert rect.height == 60
    assert rect.x == 10
    assert rect.y == 10


def test_selection_tool_resize_line():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = SelectionTool(canvas)

    line = Line(x=10, y=10, end_x=50, end_y=50)
    app_state.add_shape(line)
    app_state.select_shape(line.id)

    # Mock hit test
    canvas.hit_test = MagicMock(return_value=line)

    # Simulate hitting end handle (50, 50)
    e = MagicMock()
    tool.on_down(50, 50, e)

    assert tool.resize_handle == "end"

    # Drag to (60, 60)
    tool.on_move(60, 60, e)

    assert line.end_x == 60
    assert line.end_y == 60
    assert line.x == 10
    assert line.y == 10


def test_selection_tool_multi_select():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = SelectionTool(canvas)

    r1 = Rectangle(x=10, y=10, width=50, height=50)
    r2 = Rectangle(x=100, y=100, width=50, height=50)
    app_state.add_shape(r1)
    app_state.add_shape(r2)

    # Select r1
    canvas.hit_test = MagicMock(return_value=r1)
    e = MagicMock()
    tool.on_down(20, 20, e)
    assert app_state.selected_shape_ids == {r1.id}

    # Shift-select r2
    app_state.is_shift_down = True
    canvas.hit_test = MagicMock(return_value=r2)
    tool.on_down(120, 120, e)

    assert len(app_state.selected_shape_ids) == 2
    assert r1.id in app_state.selected_shape_ids
    assert r2.id in app_state.selected_shape_ids


def test_selection_tool_pan():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = SelectionTool(canvas)

    # Background click
    canvas.hit_test = MagicMock(return_value=None)

    # Down at screen (100, 100)
    e = MagicMock(local_x=100, local_y=100)
    tool.on_down(100, 100, e)

    assert tool._is_panning is True
    assert tool._pan_start_sx == 100
    assert tool._pan_start_sy == 100

    # Move to (150, 150) -> delta (50, 50)
    # Pan moves opposite to drag usually, but implementation says:
    # new_pan = initial + delta
    e.local_x = 150
    e.local_y = 150
    tool.on_move(150, 150, e)

    assert app_state.pan_x == 50
    assert app_state.pan_y == 50


def test_double_click_text_edit():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    # Mock page for dialog
    canvas.page = MagicMock()
    tool = SelectionTool(canvas)

    txt = Text(x=10, y=10, content="Hello")
    app_state.add_shape(txt)
    app_state.select_shape(txt.id)

    # First click
    canvas.hit_test = MagicMock(return_value=txt)
    e = MagicMock()

    import time

    tool._last_click_time = time.time() - 0.1  # Very recent click

    tool.on_down(15, 15, e)

    # Should trigger edit dialog
    assert canvas.page.open.called
    assert canvas.page.update.called


def test_resize_group():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = SelectionTool(canvas)

    r1 = Rectangle(x=0, y=0, width=50, height=50)
    r2 = Rectangle(x=50, y=0, width=50, height=50)
    group = Group(children=[r1, r2])
    # Group bounding box approx (0,0) to (100, 50)

    app_state.add_shape(group)
    app_state.select_shape(group.id)

    canvas.hit_test = MagicMock(return_value=group)

    # Hit bottom-right of group (100, 50)
    e = MagicMock()
    tool.on_down(100, 50, e)

    assert tool.resize_handle == "br"

    # Resize to (200, 100) -> 2x scale
    tool.on_move(200, 100, e)

    # Group children should be scaled
    assert r1.width == 100  # 50 * 2
    assert r1.height == 100  # 50 * 2
    assert r2.x == 100  # 50 * 2
