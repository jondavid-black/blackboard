import flet as ft
from blackboard.state.app_state import AppState
from blackboard.models import Group, Rectangle, Circle
from blackboard.ui.drawers.layers_drawer import LayersDrawer


def test_layers_drawer_nested_rendering():
    app_state = AppState()

    # Create children
    rect = Rectangle(id="rect1", type="rectangle")
    circle = Circle(id="circle1", type="circle")

    # Create group
    group = Group(id="group1", type="group", children=[rect, circle])

    # Add group to app state
    app_state.shapes = [group]
    # IMPORTANT: Expand group so children are rendered
    app_state.expanded_group_ids.add(group.id)

    drawer = LayersDrawer(app_state)

    # Get content
    content = drawer._get_layers_content()

    # Content structure: [Title, Divider, Column]
    assert len(content) == 3
    column = content[2]
    assert isinstance(column, ft.Column)

    # Controls in column:
    # 1. Group DragTarget
    # 2. Circle DragTarget (reversed order in display? reversed(shapes))
    # 3. Rect DragTarget
    # 4. Bottom Drop Target

    controls = column.controls
    # reversed([group]) -> group
    # _build_layer_tree(group) ->
    #   add group
    #   recurse children: reversed([rect, circle]) -> circle, rect

    # Expected order: Group, Circle, Rect, BottomTarget
    assert len(controls) == 4

    # 1. Group
    group_target = controls[0]
    assert isinstance(group_target, ft.DragTarget)
    assert group_target.data == "group1"

    # Check indentation of group (depth 0)
    # Container -> padding.left = 0 * 20 = 0
    group_container = group_target.content.content
    assert group_container.padding.left == 0

    # 2. Circle (First child in reversed list)
    circle_target = controls[1]
    assert isinstance(circle_target, ft.DragTarget)
    assert circle_target.data == "circle1"

    # Check indentation of child (depth 1)
    # Container -> padding.left = 1 * 20 = 20
    circle_container = circle_target.content.content
    assert circle_container.padding.left == 20

    # 3. Rect
    rect_target = controls[2]
    assert isinstance(rect_target, ft.DragTarget)
    assert rect_target.data == "rect1"

    # Check indentation of child (depth 1)
    rect_container = rect_target.content.content
    assert rect_container.padding.left == 20

    # 4. Bottom
    bottom_target = controls[3]
    assert bottom_target.data == "__BOTTOM__"
