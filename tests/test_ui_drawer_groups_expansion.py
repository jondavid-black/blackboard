from blackboard.state.app_state import AppState
from blackboard.ui.drawers.layers_drawer import LayersDrawer
from blackboard.models import Group, Rectangle
from conftest import MockStorageService


def test_layers_drawer_group_expansion_toggle():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)

    rect1 = Rectangle(id="rect1", x=0, y=0, width=10, height=10)
    group1 = Group(id="group1", type="group", children=[rect1])

    app_state.add_shape(group1)

    # Initial state: Not expanded by default? Or yes?
    # In our implementation we started with empty set, so collapsed.
    assert "group1" not in app_state.expanded_group_ids

    # Toggle expansion
    app_state.toggle_group_expansion("group1")
    assert "group1" in app_state.expanded_group_ids

    # Toggle again
    app_state.toggle_group_expansion("group1")
    assert "group1" not in app_state.expanded_group_ids


def test_layers_drawer_render_children_only_when_expanded():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)

    rect1 = Rectangle(id="rect1", x=0, y=0, width=10, height=10)
    group1 = Group(id="group1", type="group", children=[rect1])
    app_state.add_shape(group1)

    drawer = LayersDrawer(app_state)

    # 1. Collapsed (default)
    # Tree should contain Group1, but NOT Rect1
    controls = drawer._build_layer_tree(app_state.shapes, 0)
    # Controls list: [Group1_Item]
    assert len(controls) == 1
    # Check if the control is for group1
    # The drag target wraps the draggable which wraps content
    drag_target = controls[0]
    assert drag_target.data == "group1"

    # 2. Expanded
    app_state.toggle_group_expansion("group1")
    controls = drawer._build_layer_tree(app_state.shapes, 0)
    # Controls list: [Group1_Item, Rect1_Item]
    assert len(controls) == 2
    assert controls[0].data == "group1"
    assert controls[1].data == "rect1"
