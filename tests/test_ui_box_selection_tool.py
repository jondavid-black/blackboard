from unittest.mock import MagicMock
from blackboard.state.app_state import AppState
from blackboard.models import (
    Line,
    Rectangle,
    Circle,
    Polygon,
    Text,
    Path,
)
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.ui.tools.box_selection_tool import BoxSelectionTool
from conftest import MockStorageService


def test_box_selection_init():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = BoxSelectionTool(canvas)

    assert tool.box_select_start_wx is None
    assert tool.box_select_rect is None
    assert tool.is_moving_mode is False


def test_box_selection_start_empty_space():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = BoxSelectionTool(canvas)

    canvas.hit_test = MagicMock(return_value=None)

    e = MagicMock()
    tool.on_down(100, 100, e)

    assert tool.box_select_start_wx == 100
    assert tool.box_select_start_wy == 100
    assert tool.box_select_rect == (100, 100, 0, 0)
    assert tool.is_moving_mode is False


def test_box_selection_drag():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = BoxSelectionTool(canvas)

    canvas.hit_test = MagicMock(return_value=None)

    e = MagicMock()
    tool.on_down(100, 100, e)

    tool.on_move(150, 150, e)

    assert tool.box_select_rect == (100, 100, 50, 50)


def test_box_selection_selects_shapes():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = BoxSelectionTool(canvas)

    r1 = Rectangle(x=110, y=110, width=10, height=10)
    r2 = Rectangle(x=200, y=200, width=10, height=10)  # Outside
    app_state.add_shape(r1)
    app_state.add_shape(r2)

    canvas.hit_test = MagicMock(return_value=None)
    e = MagicMock()

    # Drag box from 100,100 to 150,150
    tool.on_down(100, 100, e)
    tool.on_move(150, 150, e)
    tool.on_up(150, 150, e)

    assert r1.id in app_state.selected_shape_ids
    assert r2.id not in app_state.selected_shape_ids


def test_box_selection_click_on_selected_moves_it():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = BoxSelectionTool(canvas)

    r1 = Rectangle(x=10, y=10, width=10, height=10)
    app_state.add_shape(r1)
    app_state.select_shape(r1.id)

    canvas.hit_test = MagicMock(return_value=r1)
    e = MagicMock()

    # Click on already selected shape
    tool.on_down(15, 15, e)

    assert tool.is_moving_mode is True
    assert tool.box_select_start_wx is None

    # Move it
    tool.on_move(25, 25, e)  # +10, +10

    assert r1.x == 20  # 10 + 10
    assert r1.y == 20


def test_box_selection_intersection_shapes():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = BoxSelectionTool(canvas)

    # Test intersection logic for different shapes
    line = Line(x=110, y=110, end_x=120, end_y=120)
    circle = Circle(x=110, y=110, radius_x=10, radius_y=10)
    poly = Polygon(points=[(110, 110), (120, 120), (110, 120)])
    path = Path(points=[(110, 110), (120, 120)])
    text = Text(x=110, y=110, content="Test", font_size=16)

    app_state.add_shape(line)
    app_state.add_shape(circle)
    app_state.add_shape(poly)
    app_state.add_shape(path)
    app_state.add_shape(text)

    canvas.hit_test = MagicMock(return_value=None)
    e = MagicMock()

    # Box fully covering 100,100 to 200,200
    tool.on_down(100, 100, e)
    tool.on_move(200, 200, e)
    tool.on_up(200, 200, e)

    assert line.id in app_state.selected_shape_ids
    assert circle.id in app_state.selected_shape_ids
    assert poly.id in app_state.selected_shape_ids
    assert path.id in app_state.selected_shape_ids
    assert text.id in app_state.selected_shape_ids


def test_box_selection_shift_adds_to_selection():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    tool = BoxSelectionTool(canvas)

    r1 = Rectangle(x=10, y=10, width=10, height=10)
    r2 = Rectangle(x=110, y=110, width=10, height=10)
    app_state.add_shape(r1)
    app_state.add_shape(r2)

    # Pre-select r1
    app_state.select_shape(r1.id)
    app_state.is_shift_down = True

    canvas.hit_test = MagicMock(return_value=None)
    e = MagicMock()

    # Box select r2
    tool.on_down(100, 100, e)
    tool.on_move(150, 150, e)
    tool.on_up(150, 150, e)

    assert r1.id in app_state.selected_shape_ids
    assert r2.id in app_state.selected_shape_ids
