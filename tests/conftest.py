from typing import List, Tuple, Dict, Any
from blackboard.models import Shape, Line, Rectangle, Circle, Text, Path, Polygon, Group
import dataclasses


class MockStorageService:
    def __init__(self, initial_shapes: List[Shape] = None):
        self.shapes = initial_shapes or []
        self.view_data = {"pan_x": 0.0, "pan_y": 0.0, "zoom": 1.0}
        self.saved_shapes = []
        self.saved_view = {}

        # File management mocks
        self.files = ["default.json"]
        self.current_file = "default.json"

    def _serialize_shape(self, shape: Shape) -> Dict[str, Any]:
        return dataclasses.asdict(shape)

    def _deserialize_shape(self, data: Dict[str, Any]) -> Shape:
        shape_type = data.get("type")

        if shape_type == "line":
            return Line(**data)
        elif shape_type == "rectangle":
            return Rectangle(**data)
        elif shape_type == "circle":
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
            children_data = data.pop("children", [])
            children = [self._deserialize_shape(c) for c in children_data]
            return Group(children=children, **data)
        else:
            return Shape(**data)

    def load_data(self) -> Tuple[List[Shape], Dict[str, float]]:
        return self.shapes, self.view_data

    def save_data(
        self,
        shapes: List[Shape],
        pan_x: float,
        pan_y: float,
        zoom: float,
        grid_type: str = "none",
        immediate: bool = False,
    ):
        self.saved_shapes = shapes
        self.saved_view = {
            "pan_x": pan_x,
            "pan_y": pan_y,
            "zoom": zoom,
            "grid_type": grid_type,
        }

    def list_files(self) -> List[str]:
        return self.files

    def list_folders(self) -> List[str]:
        # In a mock, we can just return a fixed list or infer from files.
        # For simplicity, let's return any explicit folders plus inferred ones.
        folders = set(self.folders) if hasattr(self, "folders") else set()
        for f in self.files:
            if "/" in f or "\\" in f:
                parts = f.replace("\\", "/").split("/")
                # Add all parent directories
                for i in range(len(parts) - 1):
                    folders.add("/".join(parts[: i + 1]))
        return sorted(list(folders))

    def get_current_filename(self) -> str:
        return self.current_file

    def create_file(self, filename: str) -> str:
        if not filename.endswith(".json"):
            filename += ".json"

        # In this mock, we just add it to the list.
        # If it has a path "folder/file.json", we assume folder creation is implicit or handled.
        if filename not in self.files:
            self.files.append(filename)
        return filename

    def create_folder(self, folder_name: str):
        if not hasattr(self, "folders"):
            self.folders = []
        if folder_name not in self.folders:
            self.folders.append(folder_name)

    def delete_folder(self, folder_name: str):
        # Remove folder and any files inside it
        if hasattr(self, "folders") and folder_name in self.folders:
            self.folders.remove(folder_name)

        # Remove files starting with folder_name/
        prefix = folder_name + "/"
        self.files = [
            f for f in self.files if not f.replace("\\", "/").startswith(prefix)
        ]

    def switch_file(self, filename: str):
        if filename in self.files:
            self.current_file = filename
        else:
            raise FileNotFoundError(f"File {filename} not found")

    def delete_file(self, filename: str):
        if filename in self.files:
            self.files.remove(filename)
            if self.current_file == filename:
                self.current_file = self.files[0] if self.files else "default.json"
