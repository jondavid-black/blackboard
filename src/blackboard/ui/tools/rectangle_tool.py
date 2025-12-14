import flet as ft
from ...models import Rectangle
from .base_tool import BaseTool


class RectangleTool(BaseTool):
    def on_down(self, wx: float, wy: float, e):
        color = (
            ft.Colors.WHITE if self.app_state.theme_mode == "dark" else ft.Colors.BLACK
        )
        self.canvas.current_drawing_shape = Rectangle(
            x=wx, y=wy, width=0, height=0, stroke_color=color
        )
        self.app_state.add_shape(self.canvas.current_drawing_shape)

    def on_move(self, wx: float, wy: float, e):
        if not self.canvas.current_drawing_shape:
            return

        shape = self.canvas.current_drawing_shape
        if not isinstance(shape, Rectangle):
            return

        current_w = wx - shape.x
        current_h = wy - shape.y

        if self.app_state.is_shift_down:
            # Force square, using the larger dimension
            max_dim = max(abs(current_w), abs(current_h))
            # Preserve direction
            current_w = max_dim if current_w >= 0 else -max_dim
            current_h = max_dim if current_h >= 0 else -max_dim

        shape.width = current_w
        shape.height = current_h
        self.app_state.notify()

    def on_up(self, wx: float, wy: float, e):
        self.canvas.current_drawing_shape = None
        self.app_state.set_shift_key(False)
        self.app_state.notify()
