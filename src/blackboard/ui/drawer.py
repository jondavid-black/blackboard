import flet as ft
from ..state.app_state import AppState


class Drawer(ft.Container):
    def __init__(self, app_state: AppState):
        self.app_state = app_state
        super().__init__(
            width=300,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=10,
            visible=False,
            # We want this to be on top, so user can see it overlaying canvas
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.BLACK54,
            ),
        )
        self._render_content()

    def did_mount(self):
        self.app_state.add_listener(self._on_state_change)
        self._update_visibility()

    def will_unmount(self):
        self.app_state.remove_listener(self._on_state_change)

    def _on_state_change(self):
        self._update_visibility()
        self._render_content()
        self.update()

    def _update_visibility(self):
        self.visible = self.app_state.active_drawer_tab is not None

    def _render_content(self):
        tab = self.app_state.active_drawer_tab

        content_map = {
            "files": [
                ft.Text("Files", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.INSERT_DRIVE_FILE),
                    title=ft.Text("Drawing 1.board"),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.INSERT_DRIVE_FILE),
                    title=ft.Text("Project A.board"),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.INSERT_DRIVE_FILE),
                    title=ft.Text("Notes.board"),
                ),
            ],
            "tools": [
                ft.Text("Tool Settings", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("Stroke Width"),
                ft.Slider(min=1, max=10, divisions=9, label="{value}"),
                ft.Text("Opacity"),
                ft.Slider(min=0, max=100, divisions=100, label="{value}%"),
            ],
            "properties": [
                ft.Text("Properties", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("Selection: None", italic=True),
                ft.Container(height=20),
                ft.Text("Canvas Info"),
                ft.Text(f"Zoom: {int(self.app_state.zoom * 100)}%"),
            ],
            "profile": [
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
            ],
        }

        current_content = content_map.get(tab, [])

        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            on_click=lambda _: self.app_state.close_drawer(),
                        )
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
                *current_content,
            ]
        )
