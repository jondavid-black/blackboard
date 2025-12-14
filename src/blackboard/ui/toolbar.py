import flet as ft
from ..state.app_state import AppState
from ..models import ToolType


class Toolbar(ft.Container):
    def __init__(self, app_state: AppState):
        self.app_state = app_state
        super().__init__(
            padding=10,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=5,
                color=ft.Colors.BLUE_GREY_300,
            ),
        )
        self._render_content()

    def did_mount(self):
        self.app_state.add_listener(self._on_state_change)

    def will_unmount(self):
        self.app_state.remove_listener(self._on_state_change)

    def _on_state_change(self):
        self._update_colors()
        self._render_content()
        self.update()

    def _update_colors(self):
        if self.app_state.theme_mode == "dark":
            self.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            self.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=5,
                color=ft.Colors.BLACK,
            )
        else:
            self.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            self.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=5,
                color=ft.Colors.BLUE_GREY_300,
            )

    def _zoom(self, factor: float):
        new_zoom = self.app_state.zoom * factor
        self.app_state.set_zoom(max(0.1, min(10.0, new_zoom)))

    def _render_content(self):
        self.content = ft.Row(
            controls=[
                self._build_tool_button(ToolType.HAND, ft.Icons.PAN_TOOL),
                self._build_tool_button(ToolType.SELECTION, ft.Icons.SELECT_ALL),
                self._build_tool_button(ToolType.PEN, ft.Icons.EDIT),
                self._build_tool_button(ToolType.ERASER, ft.Icons.AUTO_FIX_NORMAL),
                self._build_tool_button(ToolType.LINE, ft.Icons.SHOW_CHART),
                self._build_tool_button(ToolType.RECTANGLE, ft.Icons.CROP_SQUARE),
                self._build_tool_button(ToolType.CIRCLE, ft.Icons.CIRCLE_OUTLINED),
                self._build_tool_button(ToolType.POLYGON, ft.Icons.CHANGE_HISTORY),
                self._build_tool_button(ToolType.TEXT, ft.Icons.TEXT_FIELDS),
                ft.VerticalDivider(),
                ft.IconButton(
                    icon=ft.Icons.ZOOM_OUT,
                    on_click=lambda _: self._zoom(0.8),
                    tooltip="Zoom Out",
                    mouse_cursor=ft.MouseCursor.CLICK,
                ),
                ft.Text(
                    f"{int(self.app_state.zoom * 100)}%",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.IconButton(
                    icon=ft.Icons.ZOOM_IN,
                    on_click=lambda _: self._zoom(1.25),
                    tooltip="Zoom In",
                    mouse_cursor=ft.MouseCursor.CLICK,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def _build_tool_button(self, tool_type: ToolType, icon: str):
        is_selected = self.app_state.current_tool == tool_type

        # Determine colors based on theme
        is_dark = self.app_state.theme_mode == "dark"
        icon_color_default = ft.Colors.WHITE if is_dark else ft.Colors.BLACK
        bg_color_selected = ft.Colors.BLUE_900 if is_dark else ft.Colors.BLUE_50

        if tool_type == ToolType.SELECTION:
            return ft.PopupMenuButton(
                icon=icon,
                icon_color=ft.Colors.BLUE
                if self.app_state.current_tool == ToolType.SELECTION
                or self.app_state.current_tool == ToolType.BOX_SELECTION
                else icon_color_default,
                bgcolor=bg_color_selected
                if self.app_state.current_tool == ToolType.SELECTION
                or self.app_state.current_tool == ToolType.BOX_SELECTION
                else None,
                tooltip="Selection",
                items=[
                    ft.PopupMenuItem(
                        text="Object Selection",
                        on_click=lambda _: self.app_state.set_tool(ToolType.SELECTION),
                        icon=ft.Icons.SELECT_ALL,
                    ),
                    ft.PopupMenuItem(
                        text="Multi-select",
                        on_click=lambda _: self.app_state.set_tool(
                            ToolType.BOX_SELECTION
                        ),
                        icon=ft.Icons.GRID_ON,  # Assuming a grid icon for multi/box selection
                    ),
                ],
            )

        if tool_type == ToolType.LINE:
            return ft.PopupMenuButton(
                icon=icon,
                icon_color=ft.Colors.BLUE if is_selected else icon_color_default,
                bgcolor=bg_color_selected if is_selected else None,
                tooltip="Lines",
                items=[
                    ft.PopupMenuItem(
                        text="Line",
                        on_click=lambda _: self._select_line("simple"),
                    ),
                    ft.PopupMenuItem(
                        text="Arrow",
                        on_click=lambda _: self._select_line("arrow"),
                    ),
                    # Connector/Angle Connector logic is complex to implement fully now without connection points logic.
                    # But we can add the options as requested.
                    # "connector (each end of the line connects to other shapes)" - implies anchor logic.
                    # For now, let's just allow selecting the type.
                    ft.PopupMenuItem(
                        text="Connector",
                        on_click=lambda _: self._select_line("connector"),
                    ),
                    ft.PopupMenuItem(
                        text="Angle Connector",
                        on_click=lambda _: self._select_line("angle_connector"),
                    ),
                ],
            )

        if tool_type == ToolType.POLYGON:
            # Dropdown/Popup menu for shapes
            return ft.PopupMenuButton(
                icon=icon,
                icon_color=ft.Colors.BLUE if is_selected else icon_color_default,
                bgcolor=bg_color_selected if is_selected else None,
                tooltip="Shapes",
                items=[
                    ft.PopupMenuItem(
                        text="Triangle",
                        on_click=lambda _: self._select_polygon("triangle"),
                    ),
                    ft.PopupMenuItem(
                        text="Diamond",
                        on_click=lambda _: self._select_polygon("diamond"),
                    ),
                    ft.PopupMenuItem(
                        text="Pentagon",
                        on_click=lambda _: self._select_polygon("pentagon"),
                    ),
                    ft.PopupMenuItem(
                        text="Hexagon",
                        on_click=lambda _: self._select_polygon("hexagon"),
                    ),
                    ft.PopupMenuItem(
                        text="Octagon",
                        on_click=lambda _: self._select_polygon("octagon"),
                    ),
                    ft.PopupMenuItem(
                        text="Star",
                        on_click=lambda _: self._select_polygon("star"),
                    ),
                ],
            )

        return ft.IconButton(
            icon=icon,
            icon_color=ft.Colors.BLUE if is_selected else icon_color_default,
            bgcolor=bg_color_selected if is_selected else None,
            on_click=lambda _: self.app_state.set_tool(tool_type),
            tooltip=tool_type.value.capitalize(),
            mouse_cursor=ft.MouseCursor.CLICK,
        )

    def _select_line(self, line_type):
        self.app_state.set_line_type(line_type)
        self.app_state.set_tool(ToolType.LINE)

    def _select_polygon(self, poly_type):
        self.app_state.set_polygon_type(poly_type)
        self.app_state.set_tool(ToolType.POLYGON)
