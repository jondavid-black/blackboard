import math
import flet as ft
from .base_tool import BaseTool
from ...models import Line, Rectangle, Circle, Polygon


class SelectionTool(BaseTool):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.drag_start_wx = 0
        self.drag_start_wy = 0
        self.resize_handle = None
        self.resizing_shape = None
        self.moving_shapes_initial_state = {}
        # Track previous coordinates for delta calculation
        self.last_wx = 0
        self.last_wy = 0

    def on_down(self, x: float, y: float, e):
        self.last_wx = x
        self.last_wy = y
        self.resize_handle = None
        self.resizing_shape = None
        self.moving_shapes_initial_state = {}

        # 1. Check for resize handles on selected shape first
        if self.app_state.selected_shape_id:
            selected_shape = next(
                (
                    s
                    for s in self.app_state.shapes
                    if s.id == self.app_state.selected_shape_id
                ),
                None,
            )
            if selected_shape:
                handle = self._get_resize_handle(selected_shape, x, y)
                if handle:
                    self.resize_handle = handle
                    self.resizing_shape = selected_shape
                    return

        # 2. Hit test for selection
        hit_shape = self.canvas.hit_test(x, y)
        if hit_shape:
            if self.app_state.is_shift_down:
                # Toggle selection
                if hit_shape.id in self.app_state.selected_shape_ids:
                    self.app_state.selected_shape_ids.remove(hit_shape.id)
                    self.app_state.select_shapes(
                        list(self.app_state.selected_shape_ids)
                    )  # Force notify
                else:
                    current_ids = list(self.app_state.selected_shape_ids)
                    current_ids.append(hit_shape.id)
                    self.app_state.select_shapes(current_ids)
            elif hit_shape.id not in self.app_state.selected_shape_ids:
                self.app_state.select_shape(hit_shape.id)

            self.drag_start_wx = x
            self.drag_start_wy = y

            # Store initial positions for ALL selected shapes
            for s in self.app_state.shapes:
                if s.id in self.app_state.selected_shape_ids:
                    state = {"x": s.x, "y": s.y}
                    if isinstance(s, Line):
                        state.update({"end_x": s.end_x, "end_y": s.end_y})
                    elif isinstance(s, Polygon):
                        state.update({"points": list(s.points)})
                    self.moving_shapes_initial_state[s.id] = state

        else:
            self.app_state.select_shape(None)

            # Fallback to pan if background clicked
            # We initiate pan logic here locally or delegate?
            # Canvas has special handling for HandTool, but here we might want ad-hoc pan
            # or just do nothing. Legacy code allowed pan.
            # We'll use the HandTool logic logic temporarily or set a flag?
            # Actually, standard UX: Drag on background -> Box Select.
            # But the legacy code (line 950) says "Fallback to pan".
            # Let's implement ad-hoc pan for now to match legacy.
            self._is_panning = True
            self._pan_start_sx = e.local_x
            self._pan_start_sy = e.local_y
            self._pan_initial_x = self.app_state.pan_x
            self._pan_initial_y = self.app_state.pan_y

    def on_move(self, x: float, y: float, e):
        prev_wx = self.last_wx
        prev_wy = self.last_wy
        self.last_wx = x
        self.last_wy = y

        # Ad-hoc Pan
        if getattr(self, "_is_panning", False):
            dx = e.local_x - self._pan_start_sx
            dy = e.local_y - self._pan_start_sy
            self.app_state.set_pan(self._pan_initial_x + dx, self._pan_initial_y + dy)
            return

        # Resizing
        if self.resizing_shape:
            self._handle_resize(x, y)
            return

        # Moving
        if self.app_state.selected_shape_ids and self.moving_shapes_initial_state:
            dx = x - prev_wx
            dy = y - prev_wy

            if dx == 0 and dy == 0:
                return

            # Move all selected shapes
            # We use update_shape_position which handles recursion for connected lines
            # But we must be careful about double-moving.
            # See legacy code notes: "Simple fix... if a shape is ALSO in the selection set, DO NOT move it recursively"
            # The AppState internal logic handles exclusion if selected.

            for shape in self.app_state.shapes:
                if shape.id in self.app_state.selected_shape_ids:
                    self.app_state.update_shape_position(shape, dx, dy, save=False)

            self.app_state.notify(save=False)

    def on_up(self, x: float, y: float, e):
        self.resize_handle = None
        self.resizing_shape = None
        self._is_panning = False
        self.moving_shapes_initial_state = {}
        # Final save after drag/resize
        self.app_state.notify(save=True)

    def draw_overlays(self, overlay_shapes: list):
        # Draw selection handles
        for shape in self.app_state.shapes:
            if (
                self.app_state.selected_shape_id == shape.id
                or shape.id in self.app_state.selected_shape_ids
            ):
                self._draw_selection_handles(overlay_shapes, shape)

    def _draw_selection_handles(self, overlay_shapes, shape):
        import flet.canvas as cv

        handle_paint = ft.Paint(color=ft.Colors.BLUE, style=ft.PaintingStyle.FILL)
        handle_size = 8
        hs = handle_size / 2

        if isinstance(shape, Line):
            sx1, sy1 = self.canvas.to_screen(shape.x, shape.y)
            sx2, sy2 = self.canvas.to_screen(shape.end_x, shape.end_y)
            overlay_shapes.append(
                cv.Rect(
                    sx1 - hs, sy1 - hs, handle_size, handle_size, paint=handle_paint
                )
            )
            overlay_shapes.append(
                cv.Rect(
                    sx2 - hs, sy2 - hs, handle_size, handle_size, paint=handle_paint
                )
            )

        elif isinstance(shape, Rectangle):
            sx, sy = self.canvas.to_screen(shape.x, shape.y)
            w = shape.width * self.app_state.zoom
            h = shape.height * self.app_state.zoom
            self._draw_box_handles(
                overlay_shapes, sx, sy, w, h, handle_size, handle_paint
            )

        elif isinstance(shape, Circle):
            sx, sy = self.canvas.to_screen(shape.x, shape.y)
            w = shape.radius_x * 2 * self.app_state.zoom
            h = shape.radius_y * 2 * self.app_state.zoom
            self._draw_box_handles(
                overlay_shapes, sx, sy, w, h, handle_size, handle_paint
            )

        elif isinstance(shape, Polygon):
            if not shape.points:
                return
            xs = [p[0] for p in shape.points]
            ys = [p[1] for p in shape.points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

            sx1, sy1 = self.canvas.to_screen(min_x, min_y)
            w = (max_x - min_x) * self.app_state.zoom
            h = (max_y - min_y) * self.app_state.zoom
            self._draw_box_handles(
                overlay_shapes, sx1, sy1, w, h, handle_size, handle_paint
            )

    def _draw_box_handles(self, overlay_shapes, sx, sy, w, h, size, paint):
        import flet.canvas as cv

        hs = size / 2
        # TL, TR, BL, BR
        overlay_shapes.append(cv.Rect(sx - hs, sy - hs, size, size, paint=paint))
        overlay_shapes.append(cv.Rect(sx + w - hs, sy - hs, size, size, paint=paint))
        overlay_shapes.append(cv.Rect(sx - hs, sy + h - hs, size, size, paint=paint))
        overlay_shapes.append(
            cv.Rect(sx + w - hs, sy + h - hs, size, size, paint=paint)
        )

    def _get_resize_handle(self, shape, wx, wy):
        threshold = 10 / self.app_state.zoom

        if isinstance(shape, Line):
            if math.hypot(wx - shape.x, wy - shape.y) < threshold:
                return "start"
            if math.hypot(wx - shape.end_x, wy - shape.end_y) < threshold:
                return "end"

        elif isinstance(shape, Rectangle):
            x1 = shape.x
            y1 = shape.y
            x2 = shape.x + shape.width
            y2 = shape.y + shape.height

            if math.hypot(wx - x1, wy - y1) < threshold:
                return "tl"
            if math.hypot(wx - x2, wy - y1) < threshold:
                return "tr"
            if math.hypot(wx - x1, wy - y2) < threshold:
                return "bl"
            if math.hypot(wx - x2, wy - y2) < threshold:
                return "br"

        elif isinstance(shape, Circle):
            w = shape.radius_x * 2
            h = shape.radius_y * 2
            x1 = shape.x
            y1 = shape.y
            x2 = x1 + w
            y2 = y1 + h

            if math.hypot(wx - x1, wy - y1) < threshold:
                return "tl"
            if math.hypot(wx - x2, wy - y1) < threshold:
                return "tr"
            if math.hypot(wx - x1, wy - y2) < threshold:
                return "bl"
            if math.hypot(wx - x2, wy - y2) < threshold:
                return "br"

        elif isinstance(shape, Polygon):
            xs = [p[0] for p in shape.points]
            ys = [p[1] for p in shape.points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

            w = max_x - min_x
            h = max_y - min_y

            x1 = min_x
            y1 = min_y
            x2 = min_x + w
            y2 = min_y + h

            if math.hypot(wx - x1, wy - y1) < threshold:
                return "tl"
            if math.hypot(wx - x2, wy - y1) < threshold:
                return "tr"
            if math.hypot(wx - x1, wy - y2) < threshold:
                return "bl"
            if math.hypot(wx - x2, wy - y2) < threshold:
                return "br"

        return None

    def _handle_resize(self, wx, wy):
        shape = self.resizing_shape
        if isinstance(shape, Line):
            if self.resize_handle == "start":
                shape.x = wx
                shape.y = wy
            elif self.resize_handle == "end":
                shape.end_x = wx
                shape.end_y = wy

        elif isinstance(shape, Rectangle):
            # Current absolute corners
            x1 = shape.x
            y1 = shape.y
            x2 = shape.x + shape.width
            y2 = shape.y + shape.height

            if self.resize_handle == "tl":
                x1, y1 = wx, wy
            elif self.resize_handle == "tr":
                x2, y1 = wx, wy
            elif self.resize_handle == "bl":
                x1, y2 = wx, wy
            elif self.resize_handle == "br":
                x2, y2 = wx, wy

            shape.x = x1
            shape.y = y1
            shape.width = x2 - x1
            shape.height = y2 - y1

        elif isinstance(shape, Circle):
            w = shape.radius_x * 2
            h = shape.radius_y * 2
            x1 = shape.x
            y1 = shape.y
            x2 = x1 + w
            y2 = y1 + h

            if self.resize_handle == "tl":
                x1, y1 = wx, wy
            elif self.resize_handle == "tr":
                x2, y1 = wx, wy
            elif self.resize_handle == "bl":
                x1, y2 = wx, wy
            elif self.resize_handle == "br":
                x2, y2 = wx, wy

            shape.x = x1
            shape.y = y1
            shape.radius_x = (x2 - x1) / 2
            shape.radius_y = (y2 - y1) / 2

        elif isinstance(shape, Polygon):
            xs = [p[0] for p in shape.points]
            ys = [p[1] for p in shape.points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

            old_w = max_x - min_x
            old_h = max_y - min_y
            old_cx = min_x + old_w / 2
            old_cy = min_y + old_h / 2

            nx1, ny1 = min_x, min_y
            nx2, ny2 = max_x, max_y

            if self.resize_handle == "tl":
                nx1, ny1 = wx, wy
            elif self.resize_handle == "tr":
                nx2, ny1 = wx, wy
            elif self.resize_handle == "bl":
                nx1, ny2 = wx, wy
            elif self.resize_handle == "br":
                nx2, ny2 = wx, wy

            new_w = nx2 - nx1
            new_h = ny2 - ny1

            if old_w == 0:
                old_w = 0.001
            if old_h == 0:
                old_h = 0.001

            scale_x = new_w / old_w
            scale_y = new_h / old_h

            new_cx = nx1 + new_w / 2
            new_cy = ny1 + new_h / 2

            new_points = []
            for px, py in shape.points:
                dx = px - old_cx
                dy = py - old_cy
                dx *= scale_x
                dy *= scale_y
                new_points.append((new_cx + dx, new_cy + dy))

            shape.points = new_points
            shape.x = nx1
            shape.y = ny1

        self.app_state.update_shape(shape)
