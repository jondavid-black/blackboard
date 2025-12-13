from typing import List, Tuple, Dict
from blackboard.models import Shape


class MockStorageService:
    def __init__(self, initial_shapes: List[Shape] = None):
        self.shapes = initial_shapes or []
        self.view_data = {"pan_x": 0.0, "pan_y": 0.0, "zoom": 1.0}
        self.saved_shapes = []
        self.saved_view = {}

        # File management mocks
        self.files = ["default.json"]
        self.current_file = "default.json"

    def load_data(self) -> Tuple[List[Shape], Dict[str, float]]:
        return self.shapes, self.view_data

    def save_data(
        self,
        shapes: List[Shape],
        pan_x: float,
        pan_y: float,
        zoom: float,
        immediate: bool = False,
    ):
        self.saved_shapes = shapes
        self.saved_view = {"pan_x": pan_x, "pan_y": pan_y, "zoom": zoom}

    def list_files(self) -> List[str]:
        return self.files

    def get_current_filename(self) -> str:
        return self.current_file

    def create_file(self, filename: str) -> str:
        if not filename.endswith(".json"):
            filename += ".json"
        if filename not in self.files:
            self.files.append(filename)
        return filename

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
