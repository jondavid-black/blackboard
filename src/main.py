import flet as ft
from blackboard.state.app_state import AppState
from blackboard.ui.toolbar import Toolbar
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.ui.theme_switcher import ThemeSwitcher
from blackboard.ui.background import Background
from blackboard.ui.side_rail import SideRail
from blackboard.ui.drawer import Drawer


def main(page: ft.Page):
    page.title = "Blackboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0

    app_state = AppState()

    toolbar = Toolbar(app_state)
    canvas = BlackboardCanvas(app_state)
    theme_switcher = ThemeSwitcher(app_state)
    background = Background(app_state)

    side_rail = SideRail(app_state)
    drawer = Drawer(app_state)

    # Layout: Stack order matters. Background first, then Canvas, then UI overlay.
    page.add(
        ft.Stack(
            controls=[
                background,  # Bottom layer
                canvas,  # Middle layer (drawing)
                # Top layer (UI)
                # Toolbar at top center
                ft.Row(
                    controls=[toolbar],
                    alignment=ft.MainAxisAlignment.CENTER,
                    top=10,
                    left=0,
                    right=0,
                ),
                # Theme switcher at top right
                ft.Row(
                    controls=[theme_switcher],
                    alignment=ft.MainAxisAlignment.END,
                    top=10,
                    right=10,
                ),
                # Side Rail at left (overlay)
                side_rail,
                # Drawer next to Side Rail (overlay)
                # We position it absolutely. It will animate visibility.
                ft.Row(
                    controls=[drawer],
                    alignment=ft.MainAxisAlignment.START,
                    left=80,  # Assuming rail width approx 80-100. Rail min_width=100 in definition
                    top=0,
                    bottom=0,
                ),
            ],
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
