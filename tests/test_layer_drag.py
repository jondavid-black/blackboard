from unittest.mock import MagicMock
from blackboard.state.app_state import AppState
from blackboard.ui.drawers.layers_drawer import LayersDrawer
from blackboard.models import Rectangle
from conftest import MockStorageService


def test_layers_drawer_drag_reorder():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)

    # Create 3 shapes
    rect1 = Rectangle(id="rect1", x=0, y=0, width=10, height=10)
    rect2 = Rectangle(id="rect2", x=20, y=20, width=10, height=10)
    rect3 = Rectangle(id="rect3", x=40, y=40, width=10, height=10)

    # Add in order (rect1 is bottom, rect3 is top)
    app_state.add_shape(rect1)
    app_state.add_shape(rect2)
    app_state.add_shape(rect3)

    # State: [rect1, rect2, rect3]
    assert app_state.shapes == [rect1, rect2, rect3]

    drawer = LayersDrawer(app_state)

    # Simulate Drop event: Drag Rect3 (Top) onto Rect1 (Bottom)
    e = MagicMock()
    e.data = "rect3"  # The source ID being dragged
    # e.page is not used in _on_layer_drop

    # Ensure the app_state knows about the selection, as the drag handler relies on it
    app_state.select_shape("rect3")

    drawer._on_layer_drop(e, "rect1")

    # Check new order
    # Expected: [rect1, rect3, rect2]
    assert app_state.shapes[0].id == "rect1"
    assert app_state.shapes[1].id == "rect3"
    assert app_state.shapes[2].id == "rect2"


def test_layers_drawer_drag_to_bottom():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)

    rect1 = Rectangle(id="rect1", x=0, y=0, width=10, height=10)
    rect2 = Rectangle(id="rect2", x=20, y=20, width=10, height=10)

    app_state.add_shape(rect1)
    app_state.add_shape(rect2)

    # State: [rect1, rect2]

    drawer = LayersDrawer(app_state)

    # Drag Rect2 (Top) to Bottom target
    e = MagicMock()
    e.data = "rect2"  # The source ID being dragged
    # e.page is not used in _on_layer_drop

    # Ensure the app_state knows about the selection, as the drag handler relies on it
    app_state.select_shape("rect2")

    drawer._on_layer_drop(e, "__BOTTOM__")

    # Expected: [rect2, rect1]
    assert app_state.shapes[0].id == "rect2"
    assert app_state.shapes[1].id == "rect1"
