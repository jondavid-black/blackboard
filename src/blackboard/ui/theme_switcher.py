import flet as ft
from ..state.app_state import AppState


class ThemeSwitcher(ft.Container):
    def __init__(self, app_state: AppState):
        self.app_state = app_state
        super().__init__(
            padding=10,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=5,
                color=ft.Colors.BLACK,
            ),
        )
        self._render_content()

    def did_mount(self):
        self.app_state.add_listener(self._on_state_change)
        # Initialize colors
        self._update_colors()

    def will_unmount(self):
        self.app_state.remove_listener(self._on_state_change)

    def _on_state_change(self):
        self._update_colors()
        self._sync_page_theme()
        self._render_content()
        self.update()

    def _sync_page_theme(self):
        if self.page:
            self.page.theme_mode = (
                ft.ThemeMode.DARK
                if self.app_state.theme_mode == "dark"
                else ft.ThemeMode.LIGHT
            )
            self.page.update()

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

    def _toggle_theme(self):
        new_mode = "light" if self.app_state.theme_mode == "dark" else "dark"
        self.app_state.set_theme_mode(new_mode)

    def _render_content(self):
        is_dark = self.app_state.theme_mode == "dark"
        icon = ft.Icons.LIGHT_MODE if is_dark else ft.Icons.DARK_MODE
        tooltip = "Switch to Light Mode" if is_dark else "Switch to Dark Mode"
        icon_color = ft.Colors.YELLOW if is_dark else ft.Colors.BLACK

        self.content = ft.IconButton(
            icon=icon,
            icon_color=icon_color,
            on_click=lambda _: self._toggle_theme(),
            tooltip=tooltip,
            mouse_cursor=ft.MouseCursor.CLICK,
        )
