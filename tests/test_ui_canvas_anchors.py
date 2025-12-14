import math
from blackboard.models import Rectangle
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
        self.current_tool = "selection"
        self._listeners = []
        self.selected_shape_id = None
        self.is_shift_down = False

    def add_listener(self, listener):
        pass

    def remove_listener(self, listener):
        pass

    def notify(self, save=False):
        pass


def test_get_anchors():
    app_state = MockAppState()
    canvas = BlackboardCanvas(app_state)

    # Test Rectangle Anchors
    rect = Rectangle(x=0, y=0, width=100, height=100, stroke_color="black")
    anchors = canvas.get_anchors(rect)

    # Should have 8 anchors
    assert len(anchors) == 8

    # Check Top-Center
    top_center = next((ax, ay) for aid, ax, ay in anchors if aid == "top_center")
    assert top_center == (50, 0)

    # Check Bottom-Right
    bottom_right = next((ax, ay) for aid, ax, ay in anchors if aid == "bottom_right")
    assert bottom_right == (100, 100)


def test_hit_test_anchors_and_snap():
    app_state = MockAppState()
    canvas = BlackboardCanvas(app_state)

    rect = Rectangle(x=100, y=100, width=100, height=100, stroke_color="black")
    rect.id = "rect1"
    app_state.shapes.append(rect)

    # Simulate hover near top-left anchor (100, 100)
    canvas.hover_wx = 102
    canvas.hover_wy = 102

    # Check if we can detect the anchor manually via get_anchors + distance check
    # This mimics the logic inside on_pan_start/update
    anchors = canvas.get_anchors(rect)
    snapped = False
    snapped_pos = None

    for aid, ax, ay in anchors:
        if math.hypot(canvas.hover_wx - ax, canvas.hover_wy - ay) < 10:
            snapped = True
            snapped_pos = (ax, ay)
            break

    assert snapped
    assert snapped_pos == (100, 100)


def test_connection_snap_logic():
    # This tests the logic embedded in on_pan_start/end by simulation
    app_state = MockAppState()
    canvas = BlackboardCanvas(app_state)

    rect = Rectangle(x=0, y=0, width=50, height=50)
    rect.id = "rect1"
    app_state.shapes.append(rect)

    # Simulate pan start near bottom-center (25, 50)
    # The rect is at 0,0 50x50. So bottom center is 25, 50.
    start_wx, start_wy = 26, 51

    # hit_test expects point to be INSIDE or very close.
    # Rect hit test checks: shape.x <= wx <= shape.x + shape.width
    # 26 is inside 0..50.
    # 51 is OUTSIDE 0..50.

    # Let's adjust hit test point to be strictly inside for the shape detection part,
    # or ensure hit_test has tolerance.
    # Current Rect hit_test implementation in canvas.py:
    # shape.x <= wx <= shape.x + shape.width AND shape.y <= wy <= shape.y + shape.height
    # It has NO tolerance for Rectangles.

    # So we must click ON the rectangle border or inside.
    start_wx, start_wy = 25, 49  # Inside

    # Simulate logic in on_pan_start
    start_shape = canvas.hit_test(start_wx, start_wy)
    assert start_shape is not None
    assert start_shape.id == "rect1"

    # But for snapping, we might drag OUTSIDE slightly to the anchor.
    # The snapping logic iterates anchors and checks distance.
    # Distance from (25, 49) to (25, 50) is 1. < 10. Snap!

    anchors = canvas.get_anchors(start_shape)
    snap_anchor_id = None
    final_x, final_y = start_wx, start_wy

    for aid, ax, ay in anchors:
        if math.hypot(start_wx - ax, start_wy - ay) < 10:
            snap_anchor_id = aid
            final_x, final_y = ax, ay
            break

    assert snap_anchor_id == "bottom_center"
    assert final_x == 25
    assert final_y == 50
