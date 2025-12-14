from blackboard.models import Polygon
from blackboard.storage.storage_service import StorageService


def test_polygon_model_defaults():
    poly = Polygon()
    assert poly.type == "polygon"
    assert poly.points == []
    assert poly.polygon_type == "triangle"


def test_polygon_model_init():
    points = [(0, 0), (10, 0), (5, 10)]
    poly = Polygon(points=points, polygon_type="star", stroke_color="red")
    assert poly.points == points
    assert poly.polygon_type == "star"
    assert poly.stroke_color == "red"


def test_storage_service_polygon_serialization(tmp_path):
    # Setup storage service with a temp dir
    # We need to mock DATA_DIR or subclass StorageService to use tmp_path
    # But StorageService uses a global DATA_DIR or hardcoded.
    # Let's just test _serialize_shape and _deserialize_shape directly if possible
    # or monkeypatch DATA_DIR.

    # Simpler: just instantiate StorageService and test private methods or
    # check if we can verify serialization logic without writing files.

    service = StorageService()

    points = [(0.0, 0.0), (10.0, 0.0), (5.0, 10.0)]
    poly = Polygon(points=points, polygon_type="hexagon")

    serialized = service._serialize_shape(poly)
    assert serialized["type"] == "polygon"
    assert serialized["points"] == points
    assert serialized["polygon_type"] == "hexagon"

    deserialized = service._deserialize_shape(serialized)
    assert isinstance(deserialized, Polygon)
    assert deserialized.type == "polygon"
    assert deserialized.points == points
    assert deserialized.polygon_type == "hexagon"
