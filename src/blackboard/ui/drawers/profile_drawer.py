import flet as ft
from ...state.app_state import AppState
from .base_drawer import BaseDrawer


class ProfileDrawer(BaseDrawer):
    def __init__(self, app_state: AppState):
        super().__init__(app_state)

    def build(self):
        return [
            ft.Text("User Profile", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.CircleAvatar(
                content=ft.Icon(ft.Icons.PERSON, size=40),
                radius=40,
            ),
            ft.Container(height=10),
            ft.Text("User Name", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("user@example.com", color=ft.Colors.GREY),
            ft.Container(height=20),
            ft.OutlinedButton("Sign Out", icon=ft.Icons.LOGOUT),
        ]

    def update(self):
        # Placeholder: No dynamic state for profile yet
        pass
