import flet as ft
from ..state.app_state import AppState


class Drawer(ft.Container):
    def __init__(self, app_state: AppState):
        self.app_state = app_state
        self.new_file_input = ft.TextField(
            hint_text="New file...",
            height=40,
            content_padding=10,
            text_size=14,
            expand=True,
        )
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

    def _on_create_file_click(self, e):
        name = self.new_file_input.value
        if name:
            try:
                self.app_state.create_file(name)
                self.new_file_input.value = ""
                self.new_file_input.error_text = None
                self.update()
            except Exception as ex:
                self.new_file_input.error_text = str(ex)
                self.update()

    def _get_files_content(self):
        files = self.app_state.list_files()
        current_file = self.app_state.get_current_filename()

        file_list_controls = []
        for f in files:
            is_selected = f == current_file

            # Using a local variable for capturing the filename in lambda
            def make_delete_handler(fname):
                return lambda _: self.app_state.delete_file(fname)

            def make_switch_handler(fname):
                return lambda _: self.app_state.switch_file(fname)

            file_list_controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.INSERT_DRIVE_FILE,
                                color=ft.Colors.PRIMARY
                                if is_selected
                                else ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Text(
                                f,
                                color=ft.Colors.PRIMARY
                                if is_selected
                                else ft.Colors.ON_SURFACE,
                                weight=ft.FontWeight.BOLD
                                if is_selected
                                else ft.FontWeight.NORMAL,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color=ft.Colors.ERROR,
                                tooltip="Delete",
                                on_click=make_delete_handler(f),
                            ),
                        ],
                    ),
                    on_click=make_switch_handler(f),
                    padding=5,
                    border_radius=5,
                    bgcolor=ft.Colors.BLUE_GREY_700 if is_selected else None,
                    ink=True,
                )
            )

        return [
            ft.Text("Files", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row(
                controls=[
                    self.new_file_input,
                    ft.IconButton(ft.Icons.ADD, on_click=self._on_create_file_click),
                ]
            ),
            ft.Divider(),
            ft.Column(
                controls=file_list_controls,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
        ]

    def _render_content(self):
        tab = self.app_state.active_drawer_tab

        # Default content map for simple tabs
        content_map = {
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

        if tab == "files":
            current_content = self._get_files_content()
        else:
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
            ],
        )
