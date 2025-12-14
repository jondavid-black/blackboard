import flet as ft
from ...models import Circle
from .base_tool import BaseTool


class CircleTool(BaseTool):
    def on_down(self, wx: float, wy: float, e):
        color = (
            ft.Colors.WHITE if self.app_state.theme_mode == "dark" else ft.Colors.BLACK
        )
        self.canvas.current_drawing_shape = Circle(
            x=wx, y=wy, radius_x=0, radius_y=0, stroke_color=color
        )
        self.app_state.add_shape(self.canvas.current_drawing_shape)

    def on_move(self, wx: float, wy: float, e):
        if not self.canvas.current_drawing_shape:
            return

        shape = self.canvas.current_drawing_shape
        if not isinstance(shape, Circle):
            return

        # Start point (anchor)
        start_x = shape.x
        start_y = shape.y

        # Update shape to represent the NEW size
        rx = (wx - start_x) / 2
        ry = (wy - start_y) / 2

        if self.app_state.is_shift_down:
            # Constrain to perfect circle
            max_r = max(abs(rx), abs(ry))
            # Preserve sign of drag
            rx = max_r if rx >= 0 else -max_r
            ry = max_r if ry >= 0 else -max_r

        shape.radius_x = rx
        shape.radius_y = ry
        self.app_state.notify()

    def on_up(self, wx: float, wy: float, e):
        self.canvas.current_drawing_shape = None
        self.app_state.set_shift_key(False)
        self.app_state.notify()
