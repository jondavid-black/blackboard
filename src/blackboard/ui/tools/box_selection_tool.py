from .selection_tool import SelectionTool
from ...models import Rectangle, Circle, Line, Text, Polygon, Path


class BoxSelectionTool(SelectionTool):
    """
    Tool for box selection.
    Inherits from SelectionTool to support moving selected shapes if clicked.
    """

    def __init__(self, canvas):
        super().__init__(canvas)
        self.box_select_start_wx = None
        self.box_select_start_wy = None
        self.box_select_rect = None
        self.is_moving_mode = False

    def on_down(self, x: float, y: float, e):
        # 1. Check if we clicked on an existing selected shape.
        hit_shape = self.canvas.hit_test(x, y)
        clicked_on_selected = (
            hit_shape and hit_shape.id in self.app_state.selected_shape_ids
        )

        if clicked_on_selected:
            # Switch to "move" mode (temporarily treat like SELECTION tool logic for moving)
            self.is_moving_mode = True
            # Call SelectionTool's on_down to initialize move state
            # We need to manually set up what SelectionTool.on_down does for moving
            self.last_wx = x
            self.last_wy = y
            self.drag_start_wx = x
            self.drag_start_wy = y

            self.moving_shapes_initial_state = {}
            for s in self.app_state.shapes:
                if s.id in self.app_state.selected_shape_ids:
                    state = {"x": s.x, "y": s.y}
                    if isinstance(s, Line):
                        state.update({"end_x": s.end_x, "end_y": s.end_y})
                    elif isinstance(s, Polygon):
                        state.update({"points": list(s.points)})
                    self.moving_shapes_initial_state[s.id] = state

            self.box_select_start_wx = None
            self.box_select_rect = None
            return

        # 2. Start box selection
        self.is_moving_mode = False
        self.box_select_start_wx = x
        self.box_select_start_wy = y
        self.box_select_rect = (x, y, 0, 0)

        # Clear selection unless shift is held
        if not self.app_state.is_shift_down:
            self.app_state.select_shape(None)

    def on_move(self, x: float, y: float, e):
        if self.is_moving_mode:
            # Delegate to SelectionTool move logic
            super().on_move(x, y, e)
            return

        if self.box_select_start_wx is not None:
            w = x - self.box_select_start_wx
            h = y - self.box_select_start_wy
            self.box_select_rect = (
                self.box_select_start_wx,
                self.box_select_start_wy,
                w,
                h,
            )
            # Notify to trigger redraw
            self.app_state.notify()

    def on_up(self, x: float, y: float, e):
        if self.is_moving_mode:
            super().on_up(x, y, e)
            self.is_moving_mode = False
            return

        if self.box_select_start_wx is not None and self.box_select_rect:
            # Find shapes inside rect
            rx, ry, rw, rh = self.box_select_rect

            # Normalize rect
            if rw < 0:
                rx += rw
                rw = abs(rw)
            if rh < 0:
                ry += rh
                rh = abs(rh)

            found_ids = []
            for shape in self.app_state.shapes:
                if self._is_shape_in_rect(shape, rx, ry, rw, rh):
                    found_ids.append(shape.id)

            # Logic for shift key (add to selection)
            if self.app_state.is_shift_down:
                current = list(self.app_state.selected_shape_ids)
                for fid in found_ids:
                    if fid not in current:
                        current.append(fid)
                self.app_state.select_shapes(current)
            else:
                self.app_state.select_shapes(found_ids)

        self.box_select_rect = None
        self.box_select_start_wx = None
        self.app_state.notify()

    def draw_overlays(self, overlay_shapes: list):
        if self.box_select_rect:
            import flet as ft
            import flet.canvas as cv

            x, y, w, h = self.box_select_rect
            # Convert world rect to screen
            sx, sy = self.canvas.to_screen(x, y)
            sw = w * self.app_state.zoom
            sh = h * self.app_state.zoom

            # Box selection outline
            overlay_shapes.append(
                cv.Rect(
                    sx,
                    sy,
                    sw,
                    sh,
                    paint=ft.Paint(
                        style=ft.PaintingStyle.STROKE,
                        color=ft.Colors.BLUE,
                        stroke_width=1,
                    ),
                )
            )
            # Box selection fill
            overlay_shapes.append(
                cv.Rect(
                    sx,
                    sy,
                    sw,
                    sh,
                    paint=ft.Paint(
                        style=ft.PaintingStyle.FILL,
                        color=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                    ),
                )
            )

    def _is_shape_in_rect(self, shape, rx, ry, rw, rh):
        # Helper to check if shape is strictly inside rect (or intersects?)
        # Copied from legacy canvas._is_shape_in_rect

        if isinstance(shape, Rectangle):
            sx, sy, sw, sh = shape.x, shape.y, shape.width, shape.height
        elif isinstance(shape, Circle):
            sx, sy, sw, sh = shape.x, shape.y, shape.radius_x * 2, shape.radius_y * 2
        elif isinstance(shape, Line):
            sx = min(shape.x, shape.end_x)
            sy = min(shape.y, shape.end_y)
            sw = abs(shape.x - shape.end_x)
            sh = abs(shape.y - shape.end_y)
        elif isinstance(shape, Text):
            sx, sy = shape.x, shape.y
            sw = len(shape.content) * shape.font_size * 0.6  # approx
            sh = shape.font_size
        elif isinstance(shape, Polygon):
            xs = [p[0] for p in shape.points]
            ys = [p[1] for p in shape.points]
            if not xs:
                return False
            sx, sy = min(xs), min(ys)
            sw = max(xs) - min(xs)
            sh = max(ys) - min(ys)
        elif isinstance(shape, Path):
            if not shape.points:
                return False
            xs = [p[0] for p in shape.points]
            ys = [p[1] for p in shape.points]
            sx, sy = min(xs), min(ys)
            sw = max(xs) - min(xs)
            sh = max(ys) - min(ys)
        else:
            return False

        # Check intersection (AABB)
        return sx < rx + rw and sx + sw > rx and sy < ry + rh and sy + sh > ry
