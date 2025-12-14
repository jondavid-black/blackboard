import flet as ft
from ..state.app_state import AppState
from .drawers.base_drawer import BaseDrawer
from .drawers.files_drawer import FilesDrawer
from .drawers.layers_drawer import LayersDrawer
from .drawers.properties_drawer import PropertiesDrawer
from .drawers.tools_drawer import ToolsDrawer
from .drawers.profile_drawer import ProfileDrawer


class Drawer(ft.Container):
    def __init__(self, app_state: AppState, **kwargs):
        super().__init__(
            width=300,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=0,
            visible=False,
            # We want the drawer to take full height.
            # In a Stack (like in main.py), setting expand=True on a Container might be tricky
            # if parent constraints aren't passed down directly or if it's in a Row.
            # However, looking at main.py:
            # ft.Row(controls=[drawer], left=80, top=0, bottom=0)
            # This 'Row' is inside a Stack.
            # The Row itself is positioned top=0, bottom=0, so the Row has full height.
            # For the drawer (child of Row) to fill that height, it needs expand=True.
            # expand=True,  <-- This was incorrect for Row cross-axis.
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.BLACK54,
            ),
            **kwargs,
        )
        self.app_state = app_state

        # Instantiate drawer sub-components
        # We pass a callback to sub-drawers so they can trigger a UI update
        # when their internal state changes (e.g. expanding folders).
        def on_drawer_update():
            if self.visible:
                self._render_content()
            self.update()

        self.drawers: dict[str, BaseDrawer] = {
            "files": FilesDrawer(app_state, on_update_callback=on_drawer_update),
            "layers": LayersDrawer(app_state),
            "properties": PropertiesDrawer(app_state),
            "tools": ToolsDrawer(app_state),
            "profile": ProfileDrawer(app_state),
        }

        self._render_content()

    def did_mount(self):
        self.app_state.add_listener(self._on_state_change)
        self._update_visibility()

    def will_unmount(self):
        self.app_state.remove_listener(self._on_state_change)

    def _on_state_change(self):
        self._update_visibility()
        # Only rebuild content if visible to save resources
        if self.visible:
            self._render_content()
        self.update()

    def _update_visibility(self):
        self.visible = self.app_state.active_drawer_tab is not None

    def _render_content(self):
        tab = self.app_state.active_drawer_tab

        if not tab:
            self.content = ft.Container()
            return

        drawer_module = self.drawers.get(tab)
        if drawer_module:
            controls = drawer_module.build()

            # Special case padding (legacy logic preserved)
            if tab == "files":
                self.padding = 0
            else:
                self.padding = 10
        else:
            controls = [ft.Text(f"Unknown tab: {tab}")]
            self.padding = 10

        self.content = ft.Column(
            controls=[
                # Close button row
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                on_click=lambda _: self.app_state.close_drawer(),
                            )
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    padding=5,
                ),
                *controls,
            ],
            spacing=0 if tab == "files" else 10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
