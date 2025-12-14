import flet as ft
from blackboard.state.app_state import AppState


class GridSettings(ft.Container):
    def __init__(self, app_state: AppState):
        self.app_state = app_state
        super().__init__()

        self.grid_options = ft.Dropdown(
            options=[
                ft.dropdown.Option("none", "No Grid"),
                ft.dropdown.Option("line", "Line Grid"),
                ft.dropdown.Option("dot", "Dot Grid"),
            ],
            value=self.app_state.grid_type,
            on_change=self._on_grid_change,
            width=120,
            text_size=12,
            content_padding=5,
            filled=True,
            bgcolor=ft.Colors.TRANSPARENT,
            border_color=ft.Colors.TRANSPARENT,
        )

        self.content = ft.Row(
            controls=[
                ft.Icon(ft.Icons.GRID_ON, size=16),
                self.grid_options,
            ],
            spacing=5,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Style
        self.padding = ft.padding.only(left=10, right=10)
        self.border_radius = 5
        self.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE)

    def did_mount(self):
        self.app_state.add_listener(self._on_state_change)

    def will_unmount(self):
        self.app_state.remove_listener(self._on_state_change)

    def _on_state_change(self):
        self.grid_options.value = self.app_state.grid_type
        self.update()

    def _on_grid_change(self, e):
        self.app_state.set_grid_type(e.control.value)
