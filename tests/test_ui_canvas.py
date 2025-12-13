import flet as ft
import flet.canvas as flet_canvas
from unittest.mock import MagicMock
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.state.app_state import AppState
from blackboard.models import ToolType, Line
from conftest import MockStorageService


def test_canvas_initialization():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)
    assert canvas.shapes == []
    assert canvas.expand is True


def test_canvas_pan_start_drawing_line():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.set_tool(ToolType.LINE)
    canvas = BlackboardCanvas(app_state)

    # Mock event
    # Flet events are wrappers around ControlEvent with data parsed from JSON
    # We can mock the object directly since we are in Python
    e = MagicMock(spec=ft.DragStartEvent)
    e.local_x = 100
    e.local_y = 100
    e.global_x = 100
    e.global_y = 100
    e.timestamp = 0

    canvas.on_pan_start(e)

    assert len(app_state.shapes) == 1
    shape = app_state.shapes[0]
    assert isinstance(shape, Line)
    assert shape.x == 100
    assert shape.y == 100
    assert shape.end_x == 100
    assert shape.end_y == 100
    assert canvas.current_drawing_shape == shape


def test_canvas_pan_update_drawing_line():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.set_tool(ToolType.LINE)
    canvas = BlackboardCanvas(app_state)

    # Start
    e_start = MagicMock(spec=ft.DragStartEvent)
    e_start.local_x = 100
    e_start.local_y = 100
    e_start.global_x = 100
    e_start.global_y = 100
    e_start.timestamp = 0
    canvas.on_pan_start(e_start)

    # Update
    e_update = MagicMock(spec=ft.DragUpdateEvent)
    e_update.local_x = 200
    e_update.local_y = 200
    e_update.global_x = 200
    e_update.global_y = 200
    e_update.delta_x = 100
    e_update.delta_y = 100
    e_update.primary_delta = None
    e_update.timestamp = 0
    canvas.on_pan_update(e_update)

    shape = app_state.shapes[0]
    assert isinstance(shape, Line)
    assert shape.end_x == 200
    assert shape.end_y == 200


def test_canvas_render_shapes():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)

    # Mock update to avoid error
    canvas.update = lambda: None

    # Add a line to state
    line = Line(x=0, y=0, end_x=100, end_y=100)
    app_state.add_shape(line)

    # Trigger render
    canvas._on_state_change()

    assert len(canvas.shapes) == 1
    cv_line = canvas.shapes[0]
    assert isinstance(cv_line, flet_canvas.Line)
    assert cv_line.x1 == 0
    assert cv_line.y1 == 0
    assert cv_line.x2 == 100
    assert cv_line.y2 == 100


def test_canvas_draw_circle_ellipse():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.set_tool(ToolType.CIRCLE)
    canvas = BlackboardCanvas(app_state)
    canvas.update = lambda: None

    # 1. Start drawing at (100, 100)
    e_start = MagicMock(spec=ft.DragStartEvent)
    e_start.local_x = 100
    e_start.local_y = 100
    canvas.on_pan_start(e_start)

    # 2. Drag to (150, 200) -> Width 50, Height 100
    e_update = MagicMock(spec=ft.DragUpdateEvent)
    e_update.local_x = 150
    e_update.local_y = 200
    canvas.on_pan_update(e_update)

    # 3. Verify shape properties
    from blackboard.models import Circle

    shape = app_state.shapes[0]
    assert isinstance(shape, Circle)
    assert shape.x == 100
    assert shape.y == 100
    # Radius is half-width / half-height
    assert shape.radius_x == 25.0
    assert shape.radius_y == 50.0

    # 4. Render check
    canvas._on_state_change()
    cv_oval = canvas.shapes[0]
    # Check that it rendered as an Oval (not Circle)
    assert isinstance(cv_oval, flet_canvas.Oval)
    assert cv_oval.x == 100
    assert cv_oval.y == 100
    assert cv_oval.width == 50.0
    assert cv_oval.height == 100.0

    # 5. Drag left/up (negative relative coords)
    e_update.local_x = 50  # x-50
    e_update.local_y = 50  # y-50
    canvas.on_pan_update(e_update)

    assert shape.radius_x == -25.0
    assert shape.radius_y == -25.0

    canvas._on_state_change()
    cv_oval_neg = canvas.shapes[0]
    assert cv_oval_neg.width == -50.0
    assert cv_oval_neg.height == -50.0


def test_canvas_draw_circle_with_shift():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.set_tool(ToolType.CIRCLE)
    # Enable Shift key
    app_state.set_shift_key(True)

    canvas = BlackboardCanvas(app_state)
    canvas.update = lambda: None

    # 1. Start drawing at (100, 100)
    e_start = MagicMock(spec=ft.DragStartEvent)
    e_start.local_x = 100
    e_start.local_y = 100
    canvas.on_pan_start(e_start)

    # 2. Drag to (150, 200) -> Width 50, Height 100
    # With Shift, should take max dimension (100) -> 50 radius
    e_update = MagicMock(spec=ft.DragUpdateEvent)
    e_update.local_x = 150
    e_update.local_y = 200
    canvas.on_pan_update(e_update)

    # 3. Verify shape properties
    from blackboard.models import Circle

    shape = app_state.shapes[0]
    assert isinstance(shape, Circle)
    assert shape.radius_x == 50.0
    assert shape.radius_y == 50.0  # Should match largest dimension

    # 4. Render check
    canvas._on_state_change()
    cv_oval = canvas.shapes[0]
    assert cv_oval.width == 100.0
    assert cv_oval.height == 100.0
