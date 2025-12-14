import math
import flet as ft
from .base_tool import BaseTool
from ...models import Polygon


class PolygonTool(BaseTool):
    def on_down(self, x: float, y: float, e):
        color = (
            ft.Colors.WHITE if self.app_state.theme_mode == "dark" else ft.Colors.BLACK
        )
        # Create a Polygon with 0 size initially at click point.
        # We use x,y as center.
        self.canvas.current_drawing_shape = Polygon(
            x=x,
            y=y,
            points=[],
            stroke_color=color,
            polygon_type=self.app_state.selected_polygon_type,
        )
        self.app_state.add_shape(self.canvas.current_drawing_shape)

    def on_move(self, x: float, y: float, e):
        if not self.canvas.current_drawing_shape:
            return

        shape = self.canvas.current_drawing_shape
        if not isinstance(shape, Polygon):
            return

        # Anchor is center (shape.x, shape.y)
        cx = shape.x
        cy = shape.y

        rx = abs(x - cx)
        ry = abs(y - cy)

        if self.app_state.is_shift_down:
            r = max(rx, ry)
            rx = r
            ry = r

        points = self._generate_polygon_points(cx, cy, rx, ry, shape.polygon_type)
        shape.points = points
        self.app_state.notify()

    def on_up(self, x: float, y: float, e):
        self.canvas.current_drawing_shape = None
        self.app_state.notify()

    def _generate_polygon_points(self, cx, cy, rx, ry, poly_type):
        points = []

        if poly_type == "triangle":
            sides = 3
            start_angle = -math.pi / 2
        elif poly_type == "diamond":
            sides = 4
            start_angle = -math.pi / 2
        elif poly_type == "pentagon":
            sides = 5
            start_angle = -math.pi / 2
        elif poly_type == "hexagon":
            sides = 6
            start_angle = -math.pi / 2
        elif poly_type == "octagon":
            sides = 8
            start_angle = -math.pi / 2
        elif poly_type == "star":
            # Star is special
            sides = 5
            start_angle = -math.pi / 2
            inner_radius_ratio = 0.4
            step = math.pi / sides

            for i in range(2 * sides):
                angle = start_angle + i * step
                r_x = rx if i % 2 == 0 else rx * inner_radius_ratio
                r_y = ry if i % 2 == 0 else ry * inner_radius_ratio
                px = cx + r_x * math.cos(angle)
                py = cy + r_y * math.sin(angle)
                points.append((px, py))
            return points
        else:
            sides = 3
            start_angle = -math.pi / 2

        step = 2 * math.pi / sides
        for i in range(sides):
            angle = start_angle + i * step
            px = cx + rx * math.cos(angle)
            py = cy + ry * math.sin(angle)
            points.append((px, py))

        return points
