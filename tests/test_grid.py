from blackboard.state.app_state import AppState
from conftest import MockStorageService


def test_grid_type_management():
    storage = MockStorageService()
    state = AppState(storage_service=storage)

    # Default
    assert state.grid_type == "none"

    # Change to line
    state.set_grid_type("line")
    assert state.grid_type == "line"
    # Check persistence
    assert storage.saved_view["grid_type"] == "line"

    # Change to dot
    state.set_grid_type("dot")
    assert state.grid_type == "dot"
    assert storage.saved_view["grid_type"] == "dot"


def test_load_grid_type():
    storage = MockStorageService()
    storage.view_data = {"pan_x": 10.0, "pan_y": 20.0, "zoom": 1.5, "grid_type": "dot"}

    state = AppState(storage_service=storage)
    assert state.grid_type == "dot"
    assert state.pan_x == 10.0
