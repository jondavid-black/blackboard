from typing import List, Callable, Optional
from ..models import Shape, ToolType
from ..storage.storage_service import StorageService


class AppState:
    def __init__(self, storage_service: Optional[StorageService] = None):
        self.storage = storage_service or StorageService()
        self.shapes, view_data = self.storage.load_data()
        self.selected_shape_id: Optional[str] = None
        self.current_tool: ToolType = ToolType.HAND

        # Canvas transformation
        self.pan_x: float = view_data.get("pan_x", 0.0)
        self.pan_y: float = view_data.get("pan_y", 0.0)
        self.zoom: float = view_data.get("zoom", 1.0)

        # Theme
        self.theme_mode: str = "dark"  # 'dark' or 'light'
        self.is_shift_down: bool = False
        self.selected_polygon_type: str = "triangle"

        # Side Rail & Drawer
        self.active_drawer_tab: Optional[str] = None  # None means closed

        self._listeners: List[Callable[[], None]] = []

    def add_listener(self, listener: Callable[[], None]):
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[], None]):
        if listener in self._listeners:
            self._listeners.remove(listener)

    def notify(self, save: bool = False):
        for listener in self._listeners:
            listener()
        if save:
            self.storage.save_data(self.shapes, self.pan_x, self.pan_y, self.zoom)

    def set_tool(self, tool: ToolType):
        self.current_tool = tool
        # Clear selection when switching to drawing tools
        if tool != ToolType.SELECTION and tool != ToolType.HAND:
            self.selected_shape_id = None
        self.notify()

    def add_shape(self, shape: Shape):
        self.shapes.append(shape)
        self.notify(save=True)

    def remove_shape(self, shape: Shape):
        if shape in self.shapes:
            self.shapes.remove(shape)
            if self.selected_shape_id == shape.id:
                self.selected_shape_id = None
            self.notify(save=True)

    def update_shape(self, shape: Shape):
        # In a real app, we might need to find and replace,
        # but if we are modifying the object directly, we just need to notify.
        self.notify(save=True)

    def select_shape(self, shape_id: Optional[str]):
        self.selected_shape_id = shape_id
        self.notify()

    def set_pan(self, x: float, y: float):
        self.pan_x = x
        self.pan_y = y
        self.notify(save=True)

    def set_zoom(self, zoom: float):
        self.zoom = zoom
        self.notify(save=True)

    def set_theme_mode(self, mode: str):
        self.theme_mode = mode
        self.notify()

    def set_polygon_type(self, polygon_type: str):
        self.selected_polygon_type = polygon_type
        self.notify()

    def set_shift_key(self, is_down: bool):
        if self.is_shift_down != is_down:
            self.is_shift_down = is_down
            # We don't necessarily need to notify/render on key press alone
            # unless it changes cursor or active drawing preview immediately.
            # But let's notify just in case UI needs to update.
            self.notify()

    def set_active_drawer_tab(self, tab_index: Optional[str]):
        """
        Set the active tab in the side rail.
        If the same tab is clicked, toggle it closed (set to None).
        """
        if self.active_drawer_tab == tab_index:
            self.active_drawer_tab = None
        else:
            self.active_drawer_tab = tab_index
        self.notify()

    def close_drawer(self):
        self.active_drawer_tab = None
        self.notify()

    # File Management
    def list_files(self) -> List[str]:
        return self.storage.list_files()

    def list_folders(self) -> List[str]:
        return self.storage.list_folders()

    def get_current_filename(self) -> str:
        return self.storage.get_current_filename()

    def create_file(self, filename: str):
        if not filename.endswith(".json"):
            filename += ".json"
        # Save current state before switching
        self.storage.save_data(
            self.shapes, self.pan_x, self.pan_y, self.zoom, immediate=True
        )
        self.storage.create_file(filename)
        self.switch_file(filename)

    def create_folder(self, folder_name: str):
        self.storage.create_folder(folder_name)
        self.notify()

    def switch_file(self, filename: str):
        # Save current state before switching
        # We check if we are already on this file to avoid redundant saves/reloads,
        # but switch_file logic usually implies a change.
        if self.get_current_filename() != filename:
            self.storage.save_data(
                self.shapes, self.pan_x, self.pan_y, self.zoom, immediate=True
            )

        self.storage.switch_file(filename)
        self._reload_from_storage()

    def delete_file(self, filename: str):
        current_before = self.get_current_filename()
        self.storage.delete_file(filename)
        current_after = self.get_current_filename()

        # If the underlying storage switched files (because we deleted the current one), reload.
        if current_before != current_after or filename == current_before:
            self._reload_from_storage()
        else:
            # Just notify so the file list updates
            self.notify()

    def delete_folder(self, folder_name: str):
        current_before = self.get_current_filename()
        self.storage.delete_folder(folder_name)
        current_after = self.get_current_filename()

        if current_before != current_after:
            self._reload_from_storage()
        else:
            self.notify()

    def _reload_from_storage(self):
        self.shapes, view_data = self.storage.load_data()
        self.pan_x = view_data.get("pan_x", 0.0)
        self.pan_y = view_data.get("pan_y", 0.0)
        self.zoom = view_data.get("zoom", 1.0)
        self.selected_shape_id = None
        self.notify()
