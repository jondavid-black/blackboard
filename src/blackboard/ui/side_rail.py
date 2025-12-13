import flet as ft
from ..state.app_state import AppState


class SideRail(ft.Container):
    def __init__(self, app_state: AppState):
        self.app_state = app_state

        self.nav_rail = ft.NavigationRail(
            selected_index=None,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=400,
            # No leading or trailing in the rail itself
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.FOLDER_OPEN,
                    selected_icon=ft.Icons.FOLDER,
                    label="Files",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.TUNE, selected_icon=ft.Icons.TUNE, label="Tools"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SETTINGS_ETHERNET,
                    selected_icon=ft.Icons.SETTINGS_ETHERNET,
                    label="Properties",
                ),
            ],
            on_change=self._on_nav_change,
            bgcolor=ft.Colors.TRANSPARENT,
            expand=True,  # Allow rail to fill the stack
        )

        # Avatar component
        avatar_content = ft.Column(
            controls=[
                ft.Divider(),
                ft.GestureDetector(
                    mouse_cursor=ft.MouseCursor.CLICK,
                    on_tap=lambda _: self.app_state.set_active_drawer_tab("profile"),
                    content=ft.Column(
                        controls=[
                            ft.CircleAvatar(
                                content=ft.Icon(ft.Icons.PERSON),
                            ),
                            ft.Text("User", size=12),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                    ),
                ),
                ft.Container(height=20),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )

        super().__init__(
            content=ft.Stack(
                controls=[
                    self.nav_rail,
                    ft.Container(
                        content=avatar_content,
                        bottom=0,
                        left=0,
                        right=0,
                    ),
                ]
            ),
            width=100,
            bgcolor=ft.Colors.SURFACE,
        )

    def did_mount(self):
        self.app_state.add_listener(self._on_state_change)
        self._update_selection()

    def will_unmount(self):
        self.app_state.remove_listener(self._on_state_change)

    def _on_state_change(self):
        self._update_selection()
        self.update()

    def _update_selection(self):
        # Map state string indices to integer indices for NavigationRail
        tab_map = {"files": 0, "tools": 1, "properties": 2}

        if self.app_state.active_drawer_tab in tab_map:
            self.nav_rail.selected_index = tab_map[self.app_state.active_drawer_tab]
        else:
            self.nav_rail.selected_index = None

    def _on_nav_change(self, e):
        # Map integer indices back to state strings
        index_map = {0: "files", 1: "tools", 2: "properties"}

        if e.control.selected_index in index_map:
            key = index_map[e.control.selected_index]
            # Logic to toggle is in AppState, but NavigationRail enforces a selection.
            # We need to manually handle the 'toggle off' logic if we want clicking selected to unselect.
            # However, NavigationRail on_change only fires when selection CHANGES.
            # So if we click the already selected item, this event might not fire in standard Flet/Flutter?
            # Actually, Flet NavigationRail doesn't support unselecting by clicking the same item easily
            # without custom logic.
            # Let's rely on AppState. If the user clicks a different one, it switches.
            # The 'toggle' logic in AppState handles "same tab clicked -> close".
            # BUT since on_change might not fire for re-clicks, we might need a workaround or just accept
            # that we open via rail, and close via drawer button.
            # For now let's just set it.
            self.app_state.set_active_drawer_tab(key)

        # Note: If the user clicks the avatar (not a destination), this won't fire.
