from unittest.mock import MagicMock
from blackboard.state.app_state import AppState
from blackboard.ui.drawers.layers_drawer import LayersDrawer
from blackboard.models import Group, Rectangle, Circle
import flet as ft


def test_layers_drawer_renders_groups():
    storage_mock = MagicMock()
    storage_mock.load_data.return_value = ([], {})
    app_state = AppState(storage_service=storage_mock)

    # Create shapes
    rect1 = Rectangle(id="r1", type="rectangle")
    circle1 = Circle(id="c1", type="circle")

    # Create a group containing them
    group = Group(id="g1", type="group", children=[rect1, circle1])

    app_state.shapes = [group]

    drawer = LayersDrawer(app_state)
    controls = drawer._get_layers_content()

    # The controls list contains: [Text(Layers), Divider, Column(scroll)]
    assert len(controls) == 3
    column = controls[2]
    assert isinstance(column, ft.Column)

    # The column contains the layer items.
    # We expect 1 top-level item (the group) + the bottom drop target
    layer_items = column.controls

    # Filter out the bottom drop target (data="__BOTTOM__")
    shape_items = [c for c in layer_items if getattr(c, "data", "") != "__BOTTOM__"]

    assert len(shape_items) == 1
    group_item = shape_items[0]

    # Currently, it renders as a DragTarget wrapping a Draggable wrapping a Container
    assert group_item.data == "g1"


def test_layers_drawer_flat_structure_hides_children():
    """
    Verifies that currently children are NOT rendered at the top level.
    """
    storage_mock = MagicMock()
    storage_mock.load_data.return_value = ([], {})
    app_state = AppState(storage_service=storage_mock)

    rect1 = Rectangle(id="r1")
    group = Group(id="g1", children=[rect1])
    app_state.shapes = [group]

    drawer = LayersDrawer(app_state)
    column = drawer._get_layers_content()[2]

    # Get all DragTargets
    drag_targets = [c for c in column.controls if isinstance(c, ft.DragTarget)]

    # Check IDs
    ids = [dt.data for dt in drag_targets]

    assert "g1" in ids
    assert "r1" not in ids  # Children should not be at root level
