from typing import List, Callable, Optional, TYPE_CHECKING
from ..models import Shape, ToolType, Line, Polygon
from ..storage.storage_service import StorageService

if TYPE_CHECKING:
    pass


class AppState:
    def __init__(self, storage_service: Optional[StorageService] = None):
        self.storage = storage_service or StorageService()
        self.shapes, view_data = self.storage.load_data()
        self.selected_shape_ids: set[str] = set()
        self.current_tool: ToolType = ToolType.HAND

        # Canvas transformation
        self.pan_x: float = view_data.get("pan_x", 0.0)
        self.pan_y: float = view_data.get("pan_y", 0.0)
        self.zoom: float = view_data.get("zoom", 1.0)

        # Theme
        self.theme_mode: str = "dark"  # 'dark' or 'light'
        self.is_shift_down: bool = False
        self.selected_polygon_type: str = "triangle"
        self.selected_line_type: str = "simple"

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
        if (
            tool != ToolType.SELECTION
            and tool != ToolType.HAND
            and tool != ToolType.BOX_SELECTION
        ):
            self.selected_shape_ids.clear()
        self.notify()

    def add_shape(self, shape: Shape):
        self.shapes.append(shape)
        self.notify(save=True)

    def remove_shape(self, shape: Shape):
        if shape in self.shapes:
            self.shapes.remove(shape)
            if shape.id in self.selected_shape_ids:
                self.selected_shape_ids.remove(shape.id)
            self.notify(save=True)

    def update_shape_position(
        self, shape: Shape, dx: float, dy: float, save: bool = True
    ):
        """
        Updates a shape's position and any connected lines.
        """
        # Update the shape itself
        shape.x += dx
        shape.y += dy

        if isinstance(shape, Line):
            shape.end_x += dx
            shape.end_y += dy
        elif isinstance(shape, Polygon):
            new_points = [(px + dx, py + dy) for px, py in shape.points]
            shape.points = new_points

        # Update connected lines
        self._update_connected_lines(shape, dx, dy)

        self.notify(save=save)

    def _update_connected_lines(self, moved_shape: Shape, dx: float, dy: float):
        """
        Finds all lines connected to moved_shape and updates their endpoints.
        """
        # For now, we just move the line endpoints by the same delta.
        # Ideally, we would re-calculate the anchor position if an anchor ID is present.
        # But since we don't have access to the Canvas logic (get_anchors) here easily,
        # moving by delta keeps them "stuck" effectively if the shape moves rigidly.
        #
        # TODO: Refactor to allow recalculating anchor positions if the shape changes size (resize),
        # not just position. For rigid movement, dx/dy is sufficient.

        for s in self.shapes:
            if isinstance(s, Line):
                # If the line itself is selected, it will be moved explicitly by the interaction loop.
                # We should NOT move it here to avoid double-movement.
                if s.id in self.selected_shape_ids:
                    continue

                if s.start_shape_id == moved_shape.id:
                    s.x += dx
                    s.y += dy

                if s.end_shape_id == moved_shape.id:
                    s.end_x += dx
                    s.end_y += dy

    def update_shape(self, shape: Shape, save: bool = True):
        # Update connected lines if they are attached to anchors
        self._refresh_connected_lines(shape)
        self.notify(save=save)

    def _refresh_connected_lines(self, shape: Shape):
        """
        Updates endpoints of lines connected to 'shape' based on their anchor IDs.
        This allows lines to stay attached correctly when a shape is resized.
        """
        # We need to look for lines connected to this shape
        # and if they have an anchor_id, update their position.

        # Pre-calculate anchors for the shape to avoid re-calculating for every line
        anchors = shape.get_anchors()
        anchor_map = {a[0]: (a[1], a[2]) for a in anchors}

        for s in self.shapes:
            if isinstance(s, Line):
                # Check Start
                if s.start_shape_id == shape.id and s.start_anchor_id:
                    if s.start_anchor_id in anchor_map:
                        ax, ay = anchor_map[s.start_anchor_id]
                        s.x = ax
                        s.y = ay

                # Check End
                if s.end_shape_id == shape.id and s.end_anchor_id:
                    if s.end_anchor_id in anchor_map:
                        ax, ay = anchor_map[s.end_anchor_id]
                        s.end_x = ax
                        s.end_y = ay

    def select_shape(self, shape_id: Optional[str]):
        self.selected_shape_ids.clear()
        if shape_id:
            self.selected_shape_ids.add(shape_id)
        self.notify()

    def select_shapes(self, shape_ids: list[str]):
        self.selected_shape_ids.clear()
        self.selected_shape_ids.update(shape_ids)
        self.notify()

    @property
    def selected_shape_id(self) -> Optional[str]:
        # Backwards compatibility helper
        if len(self.selected_shape_ids) == 1:
            return list(self.selected_shape_ids)[0]
        return None

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

    def set_line_type(self, line_type: str):
        self.selected_line_type = line_type
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
        self.selected_shape_ids.clear()
        self.notify()
