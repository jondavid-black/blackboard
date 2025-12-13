import os
import flet as ft
from blackboard.state.app_state import AppState
from blackboard.ui.toolbar import Toolbar
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.ui.theme_switcher import ThemeSwitcher
from blackboard.ui.background import Background


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

    # Layout: Stack order matters. Background first, then Canvas, then UI overlay.
    page.add(
        ft.Stack(
            controls=[
                background,  # Bottom layer
                canvas,  # Middle layer (drawing)
                ft.Row(  # Top layer (UI)
                    controls=[toolbar],
                    alignment=ft.MainAxisAlignment.CENTER,
                    top=10,
                    left=0,
                    right=0,
                ),
                ft.Row(
                    controls=[theme_switcher],
                    alignment=ft.MainAxisAlignment.END,
                    top=10,
                    right=10,
                ),
            ],
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
