import math
import flet as ft
from ...models import Line
from .base_tool import BaseTool


class LineTool(BaseTool):
    def on_down(self, wx: float, wy: float, e):
        color = (
            ft.Colors.WHITE if self.app_state.theme_mode == "dark" else ft.Colors.BLACK
        )

        # Check for start shape connection
        start_shape = self.canvas.hit_test(wx, wy)
        start_id = start_shape.id if start_shape else None
        start_anchor_id = None

        # Check for anchor snap on start
        if start_shape:
            threshold = 10 / self.app_state.zoom
            anchors = self.canvas.get_anchors(start_shape)
            for anchor_id, ax, ay in anchors:
                if math.hypot(wx - ax, wy - ay) < threshold:
                    start_anchor_id = anchor_id
                    # Snap start point
                    wx, wy = ax, ay
                    break

        self.canvas.current_drawing_shape = Line(
            x=wx,
            y=wy,
            end_x=wx,
            end_y=wy,
            stroke_color=color,
            line_type=getattr(self.app_state, "selected_line_type", "simple"),
            start_shape_id=start_id,
            start_anchor_id=start_anchor_id,
        )
        self.app_state.add_shape(self.canvas.current_drawing_shape)

    def on_move(self, wx: float, wy: float, e):
        if not self.canvas.current_drawing_shape:
            return

        shape = self.canvas.current_drawing_shape
        if not isinstance(shape, Line):
            return

        dx = wx - shape.x
        dy = wy - shape.y

        if self.app_state.is_shift_down:
            # Snap to 45 degree increments
            angle = math.atan2(dy, dx)
            snap_angle = round(angle / (math.pi / 4)) * (math.pi / 4)
            length = math.sqrt(dx * dx + dy * dy)

            shape.end_x = shape.x + length * math.cos(snap_angle)
            shape.end_y = shape.y + length * math.sin(snap_angle)
        else:
            shape.end_x = wx
            shape.end_y = wy

        self.app_state.notify()

    def on_up(self, wx: float, wy: float, e):
        if not self.canvas.current_drawing_shape:
            return

        shape = self.canvas.current_drawing_shape
        if not isinstance(shape, Line):
            return

        # Finalize connection
        # Use last world coordinates from pan_update (self.last_wx, self.last_wy)
        # But we should ignore the line itself being drawn
        # In the original code it used self.last_wx/wy. Here we are passed wx/wy from the event,
        # which for on_pan_end might be the same as the last update?
        # Actually flet DragEndEvent doesn't have coordinates.
        # But our canvas wrapper `on_pan_end` calls `on_up` using `self.last_wx`.

        # Search for closest anchor across ALL shapes (robust snap logic)
        threshold = 10 / self.app_state.zoom

        closest_anchor_id = None
        closest_shape_id = None
        min_dist = float("inf")
        best_ax, best_ay = None, None

        for s in self.app_state.shapes:
            if s.id == shape.id:
                continue

            anchors = self.canvas.get_anchors(s)
            for anchor_id, ax, ay in anchors:
                dist = math.hypot(wx - ax, wy - ay)
                if dist < threshold and dist < min_dist:
                    min_dist = dist
                    closest_anchor_id = anchor_id
                    closest_shape_id = s.id
                    best_ax, best_ay = ax, ay

        if closest_shape_id and closest_anchor_id:
            # Snap to anchor
            shape.end_shape_id = closest_shape_id
            shape.end_anchor_id = closest_anchor_id
            shape.end_x = best_ax
            shape.end_y = best_ay
        else:
            # Fallback to simple hit test
            end_shape = self.canvas.hit_test(wx, wy, exclude_ids={shape.id})
            if end_shape:
                shape.end_shape_id = end_shape.id

        self.app_state.notify()
        self.canvas.current_drawing_shape = None

    def draw_overlays(self, overlay_shapes: list):
        # Anchor highlighting logic
        threshold = 10 / self.app_state.zoom

        # 1. Draw anchors for shape under mouse (hover)
        hit_shape = self.canvas.hit_test(self.canvas.hover_wx, self.canvas.hover_wy)
        if hit_shape:
            self._draw_anchors(overlay_shapes, hit_shape, threshold)

        # 2. Draw anchors for shape under drag end (snapping)
        if self.canvas.current_drawing_shape and isinstance(
            self.canvas.current_drawing_shape, Line
        ):
            # Snap logic: Iterate all shapes to find the closest anchor
            closest_anchor = None
            closest_shape = None
            min_dist = float("inf")

            for shape in self.app_state.shapes:
                if shape.id == self.canvas.current_drawing_shape.id:
                    continue

                anchors = self.canvas.get_anchors(shape)
                for anchor_id, ax, ay in anchors:
                    dist = math.hypot(
                        self.canvas.last_wx - ax, self.canvas.last_wy - ay
                    )
                    if dist < threshold and dist < min_dist:
                        min_dist = dist
                        closest_anchor = (ax, ay)
                        closest_shape = shape

            if closest_anchor and closest_shape:
                asx, asy = self.canvas.to_screen(closest_anchor[0], closest_anchor[1])
                # Draw a highlight circle (Green for "Snap")
                overlay_shapes.append(
                    ft.canvas.Circle(
                        asx,
                        asy,
                        radius=8,
                        paint=ft.Paint(
                            style=ft.PaintingStyle.STROKE,
                            color=ft.Colors.GREEN,
                            stroke_width=2,
                        ),
                    )
                )

                # Also draw all anchors for context if not same as hit_shape
                if closest_shape != hit_shape:
                    self._draw_anchors(
                        overlay_shapes,
                        closest_shape,
                        threshold,
                        check_hover_at_drag_end=True,
                    )

    def _draw_anchors(
        self, canvas_shapes, shape, threshold, check_hover_at_drag_end=False
    ):
        anchors = self.canvas.get_anchors(shape)
        for anchor_id, ax, ay in anchors:
            # Draw anchor point
            asx, asy = self.canvas.to_screen(ax, ay)

            target_wx, target_wy = (
                (self.canvas.last_wx, self.canvas.last_wy)
                if check_hover_at_drag_end
                else (self.canvas.hover_wx, self.canvas.hover_wy)
            )

            is_hovered = math.hypot(target_wx - ax, target_wy - ay) < threshold

            color = ft.Colors.RED if is_hovered else ft.Colors.BLUE

            canvas_shapes.append(
                ft.canvas.Circle(
                    asx,
                    asy,
                    radius=4,
                    paint=ft.Paint(style=ft.PaintingStyle.FILL, color=color),
                )
            )
