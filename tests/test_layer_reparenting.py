from blackboard.state.app_state import AppState
from blackboard.models import Rectangle, Group
from conftest import MockStorageService


def test_reparent_root_to_group():
    """Test moving a shape from root list into a group."""
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)

    # Setup:
    # Root
    #  - Group A
    #     - Rect 1
    #  - Rect 2

    rect1 = Rectangle(id="rect1", x=0, y=0, width=10, height=10)
    group_a = Group(id="group_a", type="group", children=[rect1])

    rect2 = Rectangle(id="rect2", x=20, y=20, width=10, height=10)

    app_state.add_shape(group_a)
    app_state.add_shape(rect2)

    assert len(app_state.shapes) == 2
    assert app_state.shapes[0].id == "group_a"
    assert app_state.shapes[1].id == "rect2"
    assert len(group_a.children) == 1

    # Action: Drag Rect 2 onto Rect 1 (inside Group A)
    # This should move Rect 2 into Group A, after Rect 1
    app_state.reorder_shape(source_id="rect2", target_id="rect1")

    # Verification
    # Root
    #  - Group A
    #     - Rect 1
    #     - Rect 2

    assert len(app_state.shapes) == 1
    assert app_state.shapes[0].id == "group_a"

    children = app_state.shapes[0].children
    assert len(children) == 2
    assert children[0].id == "rect1"
    assert children[1].id == "rect2"


def test_reparent_group_to_root():
    """Test moving a shape out of a group to the root list."""
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)

    # Setup:
    # Root
    #  - Rect 1
    #  - Group A
    #     - Rect 2

    rect1 = Rectangle(id="rect1", x=0, y=0, width=10, height=10)
    rect2 = Rectangle(id="rect2", x=20, y=20, width=10, height=10)
    group_a = Group(id="group_a", type="group", children=[rect2])

    app_state.add_shape(rect1)
    app_state.add_shape(group_a)

    # Action: Drag Rect 2 onto Rect 1 (Root)
    # This should move Rect 2 out of Group A, after Rect 1
    app_state.reorder_shape(source_id="rect2", target_id="rect1")

    # Verification
    # Root
    #  - Rect 1
    #  - Rect 2
    #  - Group A (empty)

    assert len(app_state.shapes) == 3
    assert app_state.shapes[0].id == "rect1"
    assert app_state.shapes[1].id == "rect2"
    assert app_state.shapes[2].id == "group_a"
    assert len(app_state.shapes[2].children) == 0


def test_prevent_recursive_move():
    """Test ensuring we can't move a group inside itself."""
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)

    # Setup:
    # Root
    #  - Group A
    #     - Rect 1

    rect1 = Rectangle(id="rect1", x=0, y=0, width=10, height=10)
    group_a = Group(id="group_a", type="group", children=[rect1])

    app_state.add_shape(group_a)

    # Action: Drag Group A onto Rect 1 (which is inside Group A)
    app_state.reorder_shape(source_id="group_a", target_id="rect1")

    # Should maintain state, no change
    assert len(app_state.shapes) == 1
    assert app_state.shapes[0].id == "group_a"
    assert app_state.shapes[0].children[0].id == "rect1"
