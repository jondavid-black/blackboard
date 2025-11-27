import os
import flet as ft
from blackboard.state.app_state import AppState
from blackboard.ui.toolbar import Toolbar
from blackboard.ui.canvas import BlackboardCanvas


def main(page: ft.Page):
    page.title = "Blackboard"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0

    app_state = AppState()

    toolbar = Toolbar(app_state)
    canvas = BlackboardCanvas(app_state)

    # Layout: Toolbar on top (or floating), Canvas fills the rest
    page.add(
        ft.Stack(
            controls=[
                canvas,
                ft.Row(
                    controls=[toolbar],
                    alignment=ft.MainAxisAlignment.CENTER,
                    top=10,
                    left=0,
                    right=0,
                ),
            ],
            expand=True,
        )
    )

    def window_event(e):
        if e.data == "close":
            os._exit(0)

    page.window.prevent_close = True
    page.window.on_event = window_event


if __name__ == "__main__":
    ft.app(target=main)
