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
        self._render_content()
        self.update()

    def _render_content(self):
        self.content = ft.Row(
            controls=[
                self._build_tool_button(ToolType.HAND, ft.Icons.PAN_TOOL),
                self._build_tool_button(ToolType.SELECTION, ft.Icons.SELECT_ALL),
                self._build_tool_button(ToolType.PEN, ft.Icons.EDIT),
                self._build_tool_button(
                    ToolType.LINE, ft.Icons.SHOW_CHART
                ),  # Closest to line
                self._build_tool_button(ToolType.RECTANGLE, ft.Icons.CROP_SQUARE),
                self._build_tool_button(ToolType.CIRCLE, ft.Icons.CIRCLE_OUTLINED),
                self._build_tool_button(ToolType.TEXT, ft.Icons.TEXT_FIELDS),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def _build_tool_button(self, tool_type: ToolType, icon: str):
        is_selected = self.app_state.current_tool == tool_type
        return ft.IconButton(
            icon=icon,
            icon_color=ft.Colors.BLUE if is_selected else ft.Colors.BLACK,
            bgcolor=ft.Colors.BLUE_50 if is_selected else None,
            on_click=lambda _: self.app_state.set_tool(tool_type),
            tooltip=tool_type.value.capitalize(),
            mouse_cursor=ft.MouseCursor.CLICK,
        )
