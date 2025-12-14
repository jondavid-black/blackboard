import json
import os
import threading
from typing import List, Dict, Any, Optional, Tuple
from ..models import Shape, Line, Rectangle, Circle, Text, Path, Polygon
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
        for root, _, files in os.walk(DATA_DIR):
            for f in files:
                if f.endswith(".json"):
                    return os.path.join(root, f)

        default_path = os.path.join(DATA_DIR, DEFAULT_FILE)
        # Create empty default file if it doesn't exist
        if not os.path.exists(default_path):
            with open(default_path, "w") as f:
                json.dump(
                    {"shapes": [], "view": {"pan_x": 0.0, "pan_y": 0.0, "zoom": 1.0}}, f
                )
        return default_path

    def list_files(self) -> List[str]:
        """
        Returns a list of all .json files relative to DATA_DIR.
        Example: ['default.json', 'folder/project.json']
        """
        file_list = []
        for root, _, files in os.walk(DATA_DIR):
            for f in files:
                if f.endswith(".json"):
                    # Get path relative to DATA_DIR
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, DATA_DIR)
                    file_list.append(rel_path)
        return sorted(file_list)

    def list_folders(self) -> List[str]:
        """
        Returns a list of all folders relative to DATA_DIR.
        Example: ['folder', 'folder/subfolder']
        """
        folder_list = []
        for root, dirs, _ in os.walk(DATA_DIR):
            for d in dirs:
                full_path = os.path.join(root, d)
                rel_path = os.path.relpath(full_path, DATA_DIR)
                folder_list.append(rel_path)
        return sorted(folder_list)

    def create_file(self, filename: str) -> str:
        if not filename.endswith(".json"):
            filename += ".json"

        path = os.path.join(DATA_DIR, filename)

        # Ensure parent directory exists
        parent_dir = os.path.dirname(path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        if os.path.exists(path):
            raise FileExistsError(f"File {filename} already exists")

        with open(path, "w") as f:
            json.dump(
                {"shapes": [], "view": {"pan_x": 0.0, "pan_y": 0.0, "zoom": 1.0}}, f
            )
        return path

    def create_folder(self, folder_name: str):
        path = os.path.join(DATA_DIR, folder_name)
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            raise FileExistsError(f"Folder {folder_name} already exists")

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
        # We need to normalize paths for comparison
        abs_current = os.path.abspath(self.current_file)
        abs_deleted = os.path.abspath(path)

        if abs_current == abs_deleted:
            self.current_file = self._get_initial_file()

    def delete_folder(self, folder_name: str):
        path = os.path.join(DATA_DIR, folder_name)
        if os.path.exists(path) and os.path.isdir(path):
            # Check if current file is inside this folder
            abs_current = os.path.abspath(self.current_file)
            abs_folder = os.path.abspath(path)

            if abs_current.startswith(abs_folder):
                self.current_file = self._get_initial_file()

            import shutil

            shutil.rmtree(path)

    def get_current_filename(self) -> str:
        # Return path relative to DATA_DIR
        return os.path.relpath(self.current_file, DATA_DIR)

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
            # Migration for old circle data that had 'radius'
            if "radius" in data:
                r = data.pop("radius")
                if "radius_x" not in data:
                    data["radius_x"] = r
                if "radius_y" not in data:
                    data["radius_y"] = r
            return Circle(**data)
        elif shape_type == "text":
            return Text(**data)
        elif shape_type == "path":
            if "points" in data:
                data["points"] = [tuple(p) for p in data["points"]]
            return Path(**data)
        elif shape_type == "polygon":
            if "points" in data:
                data["points"] = [tuple(p) for p in data["points"]]
            return Polygon(**data)
        elif shape_type == "group":
            from ..models import Group

            children_data = data.pop("children", [])
            children = [self._deserialize_shape(c) for c in children_data]
            return Group(children=children, **data)
        else:
            return Shape(**data)
