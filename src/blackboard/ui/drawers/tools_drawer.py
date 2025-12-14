import flet as ft
from ...state.app_state import AppState
from .base_drawer import BaseDrawer


class ToolsDrawer(BaseDrawer):
    def __init__(self, app_state: AppState):
        super().__init__(app_state)

    def build(self):
        return [
            ft.Text("Tool Settings", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text("Stroke Width"),
            ft.Slider(min=1, max=10, divisions=9, label="{value}"),
            ft.Text("Opacity"),
            ft.Slider(min=0, max=100, divisions=100, label="{value}%"),
        ]

    def update(self):
        # Placeholder: No dynamic state for tool settings yet
        pass
