import flet as ft
from ...models import Text, ToolType
from .base_tool import BaseTool


class TextTool(BaseTool):
    def on_down(self, wx: float, wy: float, e):
        # Text tool creates an input dialog on click (down/up combo usually, but down is fine)
        self._add_text_input(wx, wy)

    def on_move(self, wx: float, wy: float, e):
        pass

    def on_up(self, wx: float, wy: float, e):
        pass

    def _add_text_input(self, wx, wy):
        def close_dlg(e):
            self.app_state.current_tool = ToolType.SELECTION
            self.app_state.notify()
            e.page.close(dlg)

        def add_text(e):
            text = text_field.value
            if text:
                color = (
                    ft.Colors.WHITE
                    if self.app_state.theme_mode == "dark"
                    else ft.Colors.BLACK
                )
                self.app_state.add_shape(
                    Text(
                        x=wx,
                        y=wy,
                        content=text,
                        stroke_color=color,
                        font_size=16.0,
                    )
                )
            e.page.close(dlg)
            self.app_state.set_tool(ToolType.SELECTION)

        text_field = ft.TextField(
            label="Enter text", autofocus=True, on_submit=add_text
        )

        dlg = ft.AlertDialog(
            title=ft.Text("Add Text"),
            content=text_field,
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.TextButton("OK", on_click=add_text),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=lambda e: close_dlg(e)
            if self.app_state.current_tool == ToolType.TEXT
            else None,
        )

        if self.canvas.page:
            self.canvas.page.open(dlg)
            self.canvas.page.update()
