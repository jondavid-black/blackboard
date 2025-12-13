import flet as ft
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.state.app_state import AppState
from blackboard.models import Line
from conftest import MockStorageService


def test_canvas_shapes_are_visible():
    """
    Ensure that shapes added to the canvas are actually added to the shapes list
    of the base cv.Canvas class, which is what Flet uses to render.
    """
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    canvas = BlackboardCanvas(app_state)

    # Mock update to avoid Flet error
    canvas.update = lambda: None

    # Add a line
    line = Line(x=0, y=0, end_x=100, end_y=100, stroke_color="white")
    app_state.add_shape(line)

    # Trigger state change which should rebuild shapes
    canvas._on_state_change()

    # Verify the base class 'shapes' list is populated
    assert len(canvas.shapes) == 1
    # Verify it is the line we added (and not leftovers from default.json)
    assert canvas.shapes[0].x2 == 100
    assert canvas.shapes[0].y2 == 100

    # Verify the Flet canvas object type
    rendered_shape = canvas.shapes[0]
    assert isinstance(rendered_shape, ft.canvas.Line)

    # Check properties
    assert rendered_shape.x1 == 0
    assert rendered_shape.y1 == 0
    assert rendered_shape.x2 == 100
    assert rendered_shape.y2 == 100
    assert rendered_shape.paint.color == ft.Colors.WHITE
