import flet as ft
from blackboard.state.app_state import AppState


class Background(ft.Container):
    def __init__(self, app_state: AppState):
        self.app_state = app_state
        super().__init__(
            expand=True,
            bgcolor=self._get_color(),
        )

    def did_mount(self):
        self.app_state.add_listener(self._on_state_change)

    def will_unmount(self):
        self.app_state.remove_listener(self._on_state_change)

    def _on_state_change(self):
        self.bgcolor = self._get_color()
        self.update()

    def _get_color(self):
        return (
            ft.Colors.BLUE_GREY_900
            if self.app_state.theme_mode == "dark"
            else ft.Colors.WHITE
        )
