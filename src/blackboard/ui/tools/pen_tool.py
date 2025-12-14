import flet as ft
from .base_tool import BaseTool
from ...models import Path


class PenTool(BaseTool):
    def on_down(self, x: float, y: float, e):
        color = (
            ft.Colors.WHITE if self.app_state.theme_mode == "dark" else ft.Colors.BLACK
        )
        self.canvas.current_drawing_shape = Path(points=[(x, y)], stroke_color=color)
        self.app_state.add_shape(self.canvas.current_drawing_shape)

    def on_move(self, x: float, y: float, e):
        if not self.canvas.current_drawing_shape:
            return

        shape = self.canvas.current_drawing_shape
        if not isinstance(shape, Path):
            return

        # Add point if different from last
        if not shape.points or shape.points[-1] != (x, y):
            shape.points.append((x, y))
            # Notify only, no save on every move
            self.app_state.notify()

    def on_up(self, x: float, y: float, e):
        self.canvas.current_drawing_shape = None
        self.app_state.notify()
