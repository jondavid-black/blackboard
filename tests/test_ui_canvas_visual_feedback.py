import math
from unittest.mock import MagicMock
from blackboard.models import Rectangle, Line, ToolType
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.state.app_state import AppState


class MockAppState(AppState):
    def __init__(self):
        # Bypass storage
        self.shapes = []
        self.pan_x = 0
        self.pan_y = 0
        self.zoom = 1.0
        self.theme_mode = "light"
        self.current_tool = ToolType.LINE
        self._listeners = []
        self.selected_shape_id = None
        self.is_shift_down = False
        self.selected_line_type = "simple"

    def add_listener(self, listener):
        pass

    def remove_listener(self, listener):
        pass

    def notify(self, save=False):
        pass

    def add_shape(self, shape):
        self.shapes.append(shape)


def test_visual_feedback_during_line_drag():
    """
    Verify that when dragging a line, if the cursor is near another shape,
    we generate visual feedback anchors for that destination shape.
    """
    app_state = MockAppState()
    canvas = BlackboardCanvas(app_state)
    canvas.update = MagicMock()
    # Mock the page property to return None or a mock, just to be safe if code checks it
    canvas.page = MagicMock()

    # 1. Setup scene: 2 rectangles
    rect1 = Rectangle(x=0, y=0, width=50, height=50)  # Source
    rect1.id = "rect1"
    rect2 = Rectangle(x=200, y=0, width=50, height=50)  # Dest
    rect2.id = "rect2"
    app_state.shapes.extend([rect1, rect2])

    # 2. Start drawing a line from Rect1
    # Simulate Line tool active (set in mock init)

    # Manually set current_drawing_shape to simulate active drag
    line = Line(x=25, y=25, end_x=25, end_y=25)
    line.id = "line1"
    line.start_shape_id = "rect1"
    canvas.current_drawing_shape = line
    app_state.shapes.append(line)

    # 3. Simulate dragging near Rect2
    # Move cursor to (200, 25) which is inside/near Rect2
    canvas.last_wx = 202
    canvas.last_wy = 25

    # Move hover cursor away so it doesn't trigger highlighting on Rect1 (which is at 0,0)
    # canvas.hover_wx defaults to 0,0 which hits Rect1
    canvas.hover_wx = -1000
    canvas.hover_wy = -1000

    # 4. Trigger rendering logic (we can't easily capture the output of cv.Canvas shapes list
    # since it's inside _on_state_change and assigned to self.shapes property of Flet control)
    # But we can inspect `canvas.shapes` AFTER `_on_state_change` is called.

    # We need to ensure `hit_test` works.
    # Canvas.hit_test checks app_state.shapes.

    canvas._on_state_change()

    # 5. Verify shapes contains anchor points (Circles)
    # Rect1 anchors might be drawn if hover is there?
    # But here we simulate drag. `hover_wx` is default 0.
    # Our logic:
    #   if hit_test(hover_wx, hover_wy): draw anchors (Source hover)
    #   if current_drawing_shape is Line:
    #       end_shape = hit_test(last_wx, last_wy)
    #       if end_shape: draw anchors (Dest drag)

    # canvas.hover_wx is 0,0. Rect1 is at 0,0. So Rect1 is hovered.
    # Anchors for Rect1 should be drawn.
    # canvas.last_wx is 202,25. Rect2 is at 200,0. So Rect2 is hit.
    # Anchors for Rect2 should ALSO be drawn.

    # Total anchors: 8 (Rect1) + 8 (Rect2) = 16.
    # Plus the Line shape itself = 1.
    # Plus Rect1 and Rect2 shapes = 2.
    # Total shapes in canvas.shapes list ~ 19.

    # Let's count cv.Circle instances.
    import flet.canvas as cv

    circles = [s for s in canvas.shapes if isinstance(s, cv.Circle)]

    # We expect anchors.
    assert len(circles) >= 8

    # Verify at least one circle is near Rect2 (200, 0)
    # Top-left anchor of Rect2 is at 200,0.
    # In screen coords (zoom=1, pan=0), it should be 200,0.
    anchors_near_rect2 = [c for c in circles if c.x >= 200]
    assert len(anchors_near_rect2) > 0

    # Verify one anchor is RED (highlighted) because cursor (202, 25) is near Rect2 Left-Center (200, 25)?
    # Rect2 Left-Center is at (200, 25).
    # Distance to (202, 25) is 2. Threshold is 10. So it should be highlighted.

    import flet as ft

    red_anchors = [c for c in circles if c.paint.color == ft.Colors.RED]
    assert len(red_anchors) > 0

    # The highlighted anchor should be at (200, 25)
    highlighted = red_anchors[0]
    assert highlighted.x == 200
    assert highlighted.y == 25
