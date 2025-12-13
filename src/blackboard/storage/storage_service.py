import json
import os
import threading
from typing import List, Dict, Any, Optional, Tuple
from ..models import Shape, Line, Rectangle, Circle, Text, Path
import dataclasses

DATA_DIR = "data"
DEFAULT_FILE = "default.json"


class StorageService:
    def __init__(self):
        self._ensure_data_dir()
        self.current_file = self._get_initial_file()
        self._save_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def _ensure_data_dir(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

    def _get_initial_file(self) -> str:
        files = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
        if files:
            return os.path.join(DATA_DIR, files[0])

        default_path = os.path.join(DATA_DIR, DEFAULT_FILE)
        # Create empty default file if it doesn't exist
        if not os.path.exists(default_path):
            with open(default_path, "w") as f:
                json.dump(
                    {"shapes": [], "view": {"pan_x": 0.0, "pan_y": 0.0, "zoom": 1.0}}, f
                )
        return default_path

    def list_files(self) -> List[str]:
        return [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]

    def create_file(self, filename: str) -> str:
        if not filename.endswith(".json"):
            filename += ".json"

        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            raise FileExistsError(f"File {filename} already exists")

        with open(path, "w") as f:
            json.dump(
                {"shapes": [], "view": {"pan_x": 0.0, "pan_y": 0.0, "zoom": 1.0}}, f
            )
        return path

    def switch_file(self, filename: str):
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"File {filename} does not exist")
        self.current_file = path

    def delete_file(self, filename: str):
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            return  # Or raise error

        os.remove(path)

        # If we deleted the current file, switch to default or first available
        if path == self.current_file:
            self.current_file = self._get_initial_file()

    def get_current_filename(self) -> str:
        return os.path.basename(self.current_file)

    def load_data(self) -> Tuple[List[Shape], Dict[str, float]]:
        if not os.path.exists(self.current_file):
            return [], {"pan_x": 0.0, "pan_y": 0.0, "zoom": 1.0}

        try:
            with open(self.current_file, "r") as f:
                raw_data = json.load(f)

                # Handle backward compatibility (list of shapes)
                if isinstance(raw_data, list):
                    shapes = [self._deserialize_shape(item) for item in raw_data]
                    return shapes, {"pan_x": 0.0, "pan_y": 0.0, "zoom": 1.0}

                # Handle new dict structure
                if isinstance(raw_data, dict):
                    shapes_data = raw_data.get("shapes", [])
                    view_data = raw_data.get(
                        "view", {"pan_x": 0.0, "pan_y": 0.0, "zoom": 1.0}
                    )
                    shapes = [self._deserialize_shape(item) for item in shapes_data]
                    return shapes, view_data

                return [], {"pan_x": 0.0, "pan_y": 0.0, "zoom": 1.0}

        except (json.JSONDecodeError, IOError):
            return [], {"pan_x": 0.0, "pan_y": 0.0, "zoom": 1.0}

    def save_data(
        self,
        shapes: List[Shape],
        pan_x: float,
        pan_y: float,
        zoom: float,
        immediate: bool = False,
    ):
        with self._lock:
            if self._save_timer:
                self._save_timer.cancel()

            if immediate:
                self._perform_save(shapes, pan_x, pan_y, zoom)
            else:
                # Debounce save: wait 1.5 seconds
                self._save_timer = threading.Timer(
                    1.5, self._perform_save, [shapes, pan_x, pan_y, zoom]
                )
                self._save_timer.start()

    def _perform_save(
        self, shapes: List[Shape], pan_x: float, pan_y: float, zoom: float
    ):
        shapes_data = [self._serialize_shape(shape) for shape in shapes]
        full_data = {
            "view": {"pan_x": pan_x, "pan_y": pan_y, "zoom": zoom},
            "shapes": shapes_data,
        }

        try:
            with open(self.current_file, "w") as f:
                json.dump(full_data, f, indent=2)
            print(
                f"Saved {len(shapes)} shapes and view settings to {self.current_file}"
            )
        except IOError as e:
            print(f"Error saving file: {e}")

    def _serialize_shape(self, shape: Shape) -> Dict[str, Any]:
        return dataclasses.asdict(shape)

    def _deserialize_shape(self, data: Dict[str, Any]) -> Shape:
        shape_type = data.get("type")

        if shape_type == "line":
            return Line(**data)
        elif shape_type == "rectangle":
            return Rectangle(**data)
        elif shape_type == "circle":
            return Circle(**data)
        elif shape_type == "text":
            return Text(**data)
        elif shape_type == "path":
            if "points" in data:
                data["points"] = [tuple(p) for p in data["points"]]
            return Path(**data)
        else:
            return Shape(**data)
