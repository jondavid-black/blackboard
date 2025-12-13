from typing import List, Callable, Optional
from ..models import Shape, ToolType


class AppState:
    def __init__(self):
        self.shapes: List[Shape] = []
        self.selected_shape_id: Optional[str] = None
        self.current_tool: ToolType = ToolType.HAND

        # Canvas transformation
        self.pan_x: float = 0.0
        self.pan_y: float = 0.0
        self.zoom: float = 1.0

        # Theme
        self.theme_mode: str = "dark"  # 'dark' or 'light'

        # Side Rail & Drawer
        self.active_drawer_tab: Optional[str] = None  # None means closed

        self._listeners: List[Callable[[], None]] = []

    def add_listener(self, listener: Callable[[], None]):
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[], None]):
        if listener in self._listeners:
            self._listeners.remove(listener)

    def notify(self):
        for listener in self._listeners:
            listener()

    def set_tool(self, tool: ToolType):
        self.current_tool = tool
        # Clear selection when switching to drawing tools
        if tool != ToolType.SELECTION and tool != ToolType.HAND:
            self.selected_shape_id = None
        self.notify()

    def add_shape(self, shape: Shape):
        self.shapes.append(shape)
        self.notify()

    def update_shape(self, shape: Shape):
        # In a real app, we might need to find and replace,
        # but if we are modifying the object directly, we just need to notify.
        self.notify()

    def select_shape(self, shape_id: Optional[str]):
        self.selected_shape_id = shape_id
        self.notify()

    def set_pan(self, x: float, y: float):
        self.pan_x = x
        self.pan_y = y
        self.notify()

    def set_zoom(self, zoom: float):
        self.zoom = zoom
        self.notify()

    def set_theme_mode(self, mode: str):
        self.theme_mode = mode
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
