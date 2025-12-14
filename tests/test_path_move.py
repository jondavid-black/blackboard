from blackboard.state.app_state import AppState
from blackboard.models import Path
from unittest.mock import MagicMock


def test_update_shape_position_moves_path_points():
    # Setup AppState with mocked storage to avoid file I/O
    mock_storage = MagicMock()
    mock_storage.load_data.return_value = ([], {"pan_x": 0, "pan_y": 0, "zoom": 1})

    app_state = AppState(storage_service=mock_storage)

    # Create a Path
    initial_points = [(10, 10), (20, 20), (30, 10)]
    path = Path(id="path1", x=0, y=0, points=list(initial_points))
    app_state.add_shape(path)

    # Move the path
    dx = 10
    dy = 5
    app_state.update_shape_position(path, dx, dy)

    # Verify shape.x/y updated (base behavior)
    assert path.x == 10
    assert path.y == 5

    # Verify points updated
    # Expected: (20, 15), (30, 25), (40, 15)
    expected_points = [(p[0] + dx, p[1] + dy) for p in initial_points]

    assert path.points == expected_points
