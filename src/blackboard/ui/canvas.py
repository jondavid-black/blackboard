import flet as ft
import flet.canvas as cv
import math
from ..state.app_state import AppState
from ..models import ToolType, Shape, Line, Rectangle, Circle, Text, Path, Polygon


class BlackboardCanvas(cv.Canvas):
    def __init__(self, app_state: AppState):
        self.app_state = app_state
        # The gesture container MUST be transparent to allow seeing the background underneath.
        # But for gestures to work, it must have content or a color.
        # ft.Colors.TRANSPARENT captures hits in Flet if it has content, or if it is a container with size.
        # However, earlier I found that having a color (even transparent) might block things below?
        # No, transparent is fine for visibility.
        # The issue is that I set the gesture_container bgcolor to opaque in _on_state_change,
        # which sits ON TOP of the Background component (z-index wise in the stack).
        # Since gesture_container is inside the Canvas (or rather, is the content of the detector),
        # making it opaque hides the Background component at the bottom of the stack,
        # AND it hides the drawing which is done by the Canvas itself?
        # Wait, flet.canvas.Canvas draws its shapes. Where does it draw them?
        # Flet Canvas renders shapes on itself.
        # The 'content' of a Canvas is rendered ON TOP of the shapes?
        # According to Flet docs: "The content Control is positioned above the shapes."
        # AHA!
        # The gesture_container is the 'content' of the Canvas (via GestureDetector).
        # So if gesture_container has an opaque background, it covers all the shapes drawn on the Canvas!

        self.gesture_container = ft.Container(
            expand=True, bgcolor=ft.Colors.TRANSPARENT
        )

        super().__init__(
            shapes=[],
            content=ft.GestureDetector(
                content=self.gesture_container,
                on_pan_start=self.on_pan_start,
                on_pan_update=self.on_pan_update,
                on_pan_end=self.on_pan_end,
                on_hover=self.on_hover,
                on_scroll=self.on_scroll,
                drag_interval=10,
                mouse_cursor=ft.MouseCursor.BASIC,
            ),
            expand=True,
        )

        self.current_drawing_shape: Shape | None = None
        self.start_pan_x = 0
        self.start_pan_y = 0
        self.initial_pan_x = 0
        self.initial_pan_y = 0
        # For moving objects
        self.drag_start_wx = 0
        self.drag_start_wy = 0
        self.moving_shape_initial_x = 0
        self.moving_shape_initial_y = 0
        self.moving_shape_initial_end_x = 0  # For Line
        self.moving_shape_initial_end_y = 0  # For Line
        self.moving_shape_initial_points = []  # For Polygon
        self.resize_handle = None
        self.resizing_shape = None

        # Track last world coordinates for refreshing logic when modifier keys change
        self.last_wx = 0
        self.last_wy = 0
        self.hover_wx = 0
        self.hover_wy = 0

        self.box_select_start_wx = None
        self.box_select_start_wy = None
        self.box_select_rect = None

        self._is_updating_interaction = False

    def did_mount(self):
        self.app_state.add_listener(self._on_state_change)
        self._on_state_change()  # Initial render from loaded state

    def will_unmount(self):
        self.app_state.remove_listener(self._on_state_change)

    def to_world(self, sx, sy):
        wx = (sx - self.app_state.pan_x) / self.app_state.zoom
        wy = (sy - self.app_state.pan_y) / self.app_state.zoom
        return wx, wy

    def to_screen(self, wx, wy):
        sx = (wx * self.app_state.zoom) + self.app_state.pan_x
        sy = (wy * self.app_state.zoom) + self.app_state.pan_y
        return sx, sy

    def get_anchors(self, shape: Shape):
        return shape.get_anchors()

    def _draw_anchors(
        self, canvas_shapes, shape, threshold, check_hover_at_drag_end=False
    ):
        anchors = self.get_anchors(shape)
        for anchor_id, ax, ay in anchors:
            # Draw anchor point
            asx, asy = self.to_screen(ax, ay)

            # Check if hovering this anchor
            # If check_hover_at_drag_end is True, we check against last_wx/wy (drag position)
            # Otherwise we check against hover_wx/wy (mouse position)
            # Actually, during drag, hover_wx might not be updating correctly or strictly?
            # But usually drag updates last_wx.

            target_wx, target_wy = (
                (self.last_wx, self.last_wy)
                if check_hover_at_drag_end
                else (self.hover_wx, self.hover_wy)
            )

            is_hovered = math.hypot(target_wx - ax, target_wy - ay) < threshold

            color = ft.Colors.RED if is_hovered else ft.Colors.BLUE

            canvas_shapes.append(
                cv.Circle(
                    asx,
                    asy,
                    radius=4,
                    paint=ft.Paint(style=ft.PaintingStyle.FILL, color=color),
                )
            )

    def _on_state_change(self):
        # Update logic if we are in the middle of an interaction and state changed (e.g. shift key)
        if (self.current_drawing_shape or self.resizing_shape) and hasattr(
            self, "last_wx"
        ):
            self.update_active_interaction(self.last_wx, self.last_wy)

        # Update canvas background based on theme
        if self.app_state.theme_mode == "dark":
            self.gesture_container.bgcolor = ft.Colors.TRANSPARENT
        else:
            self.gesture_container.bgcolor = ft.Colors.TRANSPARENT

        # Rebuild canvas shapes based on state

        canvas_shapes = []

        # Determine stroke color based on theme

        default_stroke_color = (
            ft.Colors.WHITE if self.app_state.theme_mode == "dark" else ft.Colors.BLACK
        )

        # Hover logic for anchors
        if self.app_state.current_tool == ToolType.LINE:
            # Check if we are hovering a shape to show anchors
            threshold = 10 / self.app_state.zoom

            # Find shape under mouse
            hit_shape = self.hit_test(self.hover_wx, self.hover_wy)

            if hit_shape:
                self._draw_anchors(canvas_shapes, hit_shape, threshold)

            # ALSO show anchors for shape under drag end if we are dragging a line
            if self.current_drawing_shape and isinstance(
                self.current_drawing_shape, Line
            ):
                # We need to find the shape under the current end position
                # self.last_wx, self.last_wy track the current drag position
                end_shape = self.hit_test(
                    self.last_wx,
                    self.last_wy,
                    exclude_ids={self.current_drawing_shape.id},
                )
                if end_shape and end_shape != hit_shape:
                    self._draw_anchors(
                        canvas_shapes,
                        end_shape,
                        threshold,
                        check_hover_at_drag_end=True,
                    )

        for shape in self.app_state.shapes:
            # Use shape color if set, otherwise default based on theme
            stroke_color = (
                shape.stroke_color if shape.stroke_color else default_stroke_color
            )

            # If the shape color was explicitly "black" or "white" (maybe from previous saves),
            # we might want to adapt it if it matches the background.
            # But for now, let's assume shape.stroke_color is what the user wants
            # unless it's the default "black" from models. Let's look at models.py.

            # Actually, let's just override it if it's the "default" for the opposite theme.
            # Simpler: if shape.stroke_color is None or empty, use default.
            # If shape.stroke_color was saved as Black on a White canvas, and we switch to Dark,
            # it will be invisible.

            # Let's enforce the theme contrast for now if the color matches the background?
            # Or better, let's rely on the fact that we should update the shape's color
            # when adding it, or just interpret it dynamically here.

            # Dynamic interpretation:
            final_color = stroke_color
            if self.app_state.theme_mode == "dark" and stroke_color == ft.Colors.BLACK:
                final_color = ft.Colors.WHITE
            elif (
                self.app_state.theme_mode == "light" and stroke_color == ft.Colors.WHITE
            ):
                final_color = ft.Colors.BLACK

            # If the color is still empty (from empty string default), set it to the theme default
            if not final_color:
                final_color = default_stroke_color

            paint = ft.Paint(
                color=final_color,
                stroke_width=shape.stroke_width,
                style=ft.PaintingStyle.STROKE,
            )

            if (
                self.app_state.selected_shape_id == shape.id
                or shape.id in self.app_state.selected_shape_ids
            ):
                paint.color = ft.Colors.BLUE
                if self.app_state.is_shift_down:
                    paint.color = ft.Colors.CYAN
                paint.stroke_width = shape.stroke_width + 2

            if isinstance(shape, Line):
                sx1, sy1 = self.to_screen(shape.x, shape.y)
                sx2, sy2 = self.to_screen(shape.end_x, shape.end_y)

                line_type = getattr(shape, "line_type", "simple")

                if line_type == "angle_connector":
                    # Draw orthogonal connector (Z-shape or L-shape)
                    # Simple heuristic: midpoint X
                    mid_x = (sx1 + sx2) / 2

                    # Points: (sx1, sy1) -> (mid_x, sy1) -> (mid_x, sy2) -> (sx2, sy2)
                    canvas_shapes.append(cv.Line(sx1, sy1, mid_x, sy1, paint=paint))
                    canvas_shapes.append(cv.Line(mid_x, sy1, mid_x, sy2, paint=paint))
                    canvas_shapes.append(cv.Line(mid_x, sy2, sx2, sy2, paint=paint))

                    # Add arrow head if it's implicitly an arrow?
                    # Usually connectors have arrows. Let's assume Angle Connector has arrow at end?
                    # The requirement "Angle Connector" doesn't explicitly say arrow, but usually it implies direction.
                    # Let's add arrow head for consistency with "Connector" logic if we add it there.
                    # For now, only if explicitly requested or let's stick to simple lines for Angle Connector unless specified.
                    # Wait, "Arrow" is a separate type. "Angle Connector" is separate.
                    # If the user wants an Arrow Angle Connector, that's a combo.
                    # Current model only has one `line_type`.
                    # Let's assume Connector types might need arrow heads?
                    # Let's just draw lines for now.

                else:
                    # Simple, Arrow, Connector (straight)
                    canvas_shapes.append(cv.Line(sx1, sy1, sx2, sy2, paint=paint))

                    # Arrow head logic
                    if line_type == "arrow":
                        # Draw arrow head at end
                        dx = sx2 - sx1
                        dy = sy2 - sy1
                        angle = math.atan2(dy, dx)
                        arrow_len = 15
                        arrow_angle = math.pi / 6

                        ax1 = sx2 - arrow_len * math.cos(angle - arrow_angle)
                        ay1 = sy2 - arrow_len * math.sin(angle - arrow_angle)
                        ax2 = sx2 - arrow_len * math.cos(angle + arrow_angle)
                        ay2 = sy2 - arrow_len * math.sin(angle + arrow_angle)

                        canvas_shapes.append(cv.Line(sx2, sy2, ax1, ay1, paint=paint))
                        canvas_shapes.append(cv.Line(sx2, sy2, ax2, ay2, paint=paint))

                # Draw handles if selected (only if single selection)
                if self.app_state.selected_shape_id == shape.id:
                    handle_paint = ft.Paint(
                        color=ft.Colors.BLUE, style=ft.PaintingStyle.FILL
                    )

                    handle_size = 8
                    hs = handle_size / 2
                    canvas_shapes.append(
                        cv.Rect(
                            sx1 - hs,
                            sy1 - hs,
                            handle_size,
                            handle_size,
                            paint=handle_paint,
                        )
                    )
                    canvas_shapes.append(
                        cv.Rect(
                            sx2 - hs,
                            sy2 - hs,
                            handle_size,
                            handle_size,
                            paint=handle_paint,
                        )
                    )

            elif isinstance(shape, Rectangle):
                sx, sy = self.to_screen(shape.x, shape.y)
                w = shape.width * self.app_state.zoom
                h = shape.height * self.app_state.zoom
                canvas_shapes.append(cv.Rect(sx, sy, w, h, paint=paint))

                # Draw handles if selected (only if single selection)
                if self.app_state.selected_shape_id == shape.id:
                    handle_paint = ft.Paint(
                        color=ft.Colors.BLUE, style=ft.PaintingStyle.FILL
                    )

                    handle_size = 8
                    hs = handle_size / 2

                    # 4 Corners
                    canvas_shapes.append(
                        cv.Rect(
                            sx - hs,
                            sy - hs,
                            handle_size,
                            handle_size,
                            paint=handle_paint,
                        )
                    )  # TL
                    canvas_shapes.append(
                        cv.Rect(
                            sx + w - hs,
                            sy - hs,
                            handle_size,
                            handle_size,
                            paint=handle_paint,
                        )
                    )  # TR
                    canvas_shapes.append(
                        cv.Rect(
                            sx - hs,
                            sy + h - hs,
                            handle_size,
                            handle_size,
                            paint=handle_paint,
                        )
                    )  # BL
                    canvas_shapes.append(
                        cv.Rect(
                            sx + w - hs,
                            sy + h - hs,
                            handle_size,
                            handle_size,
                            paint=handle_paint,
                        )
                    )  # BR

            elif isinstance(shape, Circle):
                # ... existing oval render ...
                sx, sy = self.to_screen(shape.x, shape.y)
                w = shape.radius_x * 2 * self.app_state.zoom
                h = shape.radius_y * 2 * self.app_state.zoom
                canvas_shapes.append(cv.Oval(sx, sy, w, h, paint=paint))

                # Draw handles if selected
                if (
                    self.app_state.selected_shape_id == shape.id
                    or shape.id in self.app_state.selected_shape_ids
                ):
                    handle_paint = ft.Paint(
                        color=ft.Colors.BLUE, style=ft.PaintingStyle.FILL
                    )

                    handle_size = 8
                    hs = handle_size / 2

                    # 4 Corners of bounding box
                    canvas_shapes.append(
                        cv.Rect(
                            sx - hs,
                            sy - hs,
                            handle_size,
                            handle_size,
                            paint=handle_paint,
                        )
                    )  # TL
                    canvas_shapes.append(
                        cv.Rect(
                            sx + w - hs,
                            sy - hs,
                            handle_size,
                            handle_size,
                            paint=handle_paint,
                        )
                    )  # TR
                    canvas_shapes.append(
                        cv.Rect(
                            sx - hs,
                            sy + h - hs,
                            handle_size,
                            handle_size,
                            paint=handle_paint,
                        )
                    )  # BL
                    canvas_shapes.append(
                        cv.Rect(
                            sx + w - hs,
                            sy + h - hs,
                            handle_size,
                            handle_size,
                            paint=handle_paint,
                        )
                    )  # BR

            # Text not fully implemented in canvas.Canvas yet in some versions,
            # but let's assume it is or skip for now.
            # Actually ft.canvas.Text exists.
            elif isinstance(shape, Text):
                sx, sy = self.to_screen(shape.x, shape.y)
                canvas_shapes.append(
                    cv.Text(
                        sx,
                        sy,
                        shape.content,
                        style=ft.TextStyle(
                            size=shape.font_size * self.app_state.zoom,
                            color=final_color,
                        ),
                    )
                )

            elif isinstance(shape, Path):
                if not shape.points:
                    continue

                points = [
                    ft.Offset(x, y)
                    for x, y in [self.to_screen(px, py) for px, py in shape.points]
                ]

                canvas_shapes.append(
                    cv.Points(
                        points=points,  # type: ignore
                        point_mode=cv.PointMode.POLYGON,
                        paint=paint,
                    )
                )

            elif isinstance(shape, Polygon):
                if not shape.points:
                    continue

                points = [
                    ft.Offset(x, y)
                    for x, y in [self.to_screen(px, py) for px, py in shape.points]
                ]

                # Ensure it's closed
                if len(points) > 2:
                    points.append(points[0])

                canvas_shapes.append(
                    cv.Points(
                        points=points,  # type: ignore
                        point_mode=cv.PointMode.POLYGON,
                        paint=paint,
                    )
                )

                # Draw handles if selected (similar to Rectangle/Circle bounding box)
                if (
                    self.app_state.selected_shape_id == shape.id
                    or shape.id in self.app_state.selected_shape_ids
                ):
                    handle_paint = ft.Paint(
                        color=ft.Colors.BLUE, style=ft.PaintingStyle.FILL
                    )

                    handle_size = 8
                    hs = handle_size / 2

                    # Calculate bounding box of polygon
                    xs = [p[0] for p in shape.points]
                    ys = [p[1] for p in shape.points]
                    min_x, max_x = min(xs), max(xs)
                    min_y, max_y = min(ys), max(ys)

                    sx1, sy1 = self.to_screen(min_x, min_y)
                    w = (max_x - min_x) * self.app_state.zoom
                    h = (max_y - min_y) * self.app_state.zoom

                    # 4 Corners of bounding box
                    canvas_shapes.append(
                        cv.Rect(
                            sx1 - hs,
                            sy1 - hs,
                            handle_size,
                            handle_size,
                            paint=handle_paint,
                        )
                    )  # TL
                    canvas_shapes.append(
                        cv.Rect(
                            sx1 + w - hs,
                            sy1 - hs,
                            handle_size,
                            handle_size,
                            paint=handle_paint,
                        )
                    )  # TR
                    canvas_shapes.append(
                        cv.Rect(
                            sx1 - hs,
                            sy1 + h - hs,
                            handle_size,
                            handle_size,
                            paint=handle_paint,
                        )
                    )  # BL
                    canvas_shapes.append(
                        cv.Rect(
                            sx1 + w - hs,
                            sy1 + h - hs,
                            handle_size,
                            handle_size,
                            paint=handle_paint,
                        )
                    )  # BR

        if self.box_select_rect:
            x, y, w, h = self.box_select_rect
            # Convert world rect to screen
            sx, sy = self.to_screen(x, y)
            sw = w * self.app_state.zoom
            sh = h * self.app_state.zoom

            # Use negative width/height support of cv.Rect
            canvas_shapes.append(
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
            # Add semi-transparent fill
            canvas_shapes.append(
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

        self.shapes = canvas_shapes
        self.update()

    def get_resize_handle(self, shape, wx, wy):
        threshold = 10 / self.app_state.zoom

        if isinstance(shape, Line):
            if math.hypot(wx - shape.x, wy - shape.y) < threshold:
                return "start"
            if math.hypot(wx - shape.end_x, wy - shape.end_y) < threshold:
                return "end"

        elif isinstance(shape, Rectangle):
            # Normalization for negative width/height handled by absolute coords?
            # No, shape.x/y is anchor. width/height can be negative.
            # Let's get actual corners.
            x1 = shape.x
            y1 = shape.y
            x2 = shape.x + shape.width
            y2 = shape.y + shape.height

            # We need to test all 4 corners
            if math.hypot(wx - x1, wy - y1) < threshold:
                return "tl"  # Top-Left (relative to anchor, might strictly be just "start-corner")
            if math.hypot(wx - x2, wy - y1) < threshold:
                return "tr"
            if math.hypot(wx - x1, wy - y2) < threshold:
                return "bl"
            if math.hypot(wx - x2, wy - y2) < threshold:
                return "br"

        # Circle resizing logic can be similar to Rectangle (bounding box)
        elif isinstance(shape, Circle):
            # shape.x, shape.y are top-left of bounding box
            # dimensions: 2*rx, 2*ry
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
            # Similar to Circle/Rectangle, use bounding box
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

    def hit_test(self, wx, wy, exclude_ids=None):
        if exclude_ids is None:
            exclude_ids = set()
        else:
            exclude_ids = set(exclude_ids)

        # Simple hit test
        for shape in reversed(self.app_state.shapes):
            if shape.id in exclude_ids:
                continue

            if isinstance(shape, Rectangle):
                if (
                    shape.x <= wx <= shape.x + shape.width
                    and shape.y <= wy <= shape.y + shape.height
                ):
                    return shape
            elif isinstance(shape, Circle):
                # Hit test for Ellipse/Oval
                # (x - h)^2 / a^2 + (y - k)^2 / b^2 <= 1
                # (h, k) is center.
                # shape.x, shape.y are Top-Left.
                # a = radius_x, b = radius_y
                rx = shape.radius_x
                ry = shape.radius_y

                # Avoid division by zero
                if rx == 0 or ry == 0:
                    continue

                cx = shape.x + rx
                cy = shape.y + ry

                dx = wx - cx
                dy = wy - cy

                # Check if point is inside
                if (dx * dx) / (rx * rx) + (dy * dy) / (ry * ry) <= 1:
                    return shape

            elif isinstance(shape, Line):
                # Distance from point to line segment
                # https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
                x1, y1 = shape.x, shape.y
                x2, y2 = shape.end_x, shape.end_y

                # Length of line squared
                l2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
                if l2 == 0:
                    return (
                        shape
                        if math.sqrt((wx - x1) ** 2 + (wy - y1) ** 2) < 5
                        else None
                    )

                # Projection
                t = ((wx - x1) * (x2 - x1) + (wy - y1) * (y2 - y1)) / l2
                t = max(0, min(1, t))
                px = x1 + t * (x2 - x1)
                py = y1 + t * (y2 - y1)

                dist = math.sqrt((wx - px) ** 2 + (wy - py) ** 2)
                if dist < 5 / self.app_state.zoom:  # Tolerance
                    return shape
            elif isinstance(shape, Text):
                # Approximate text bounds
                if (
                    shape.x
                    <= wx
                    <= shape.x + (len(shape.content) * shape.font_size * 0.6)
                    and shape.y <= wy <= shape.y + shape.font_size
                ):
                    return shape

            elif isinstance(shape, Path):
                if not shape.points:
                    continue

                # Check distance to any point
                threshold = 10 / self.app_state.zoom
                for px, py in shape.points:
                    if math.hypot(wx - px, wy - py) < threshold:
                        return shape

                # Check distance to segments
                for i in range(len(shape.points) - 1):
                    p1 = shape.points[i]
                    p2 = shape.points[i + 1]

                    x1, y1 = p1
                    x2, y2 = p2

                    # Distance from point to segment logic (reused from Line)
                    l2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
                    if l2 == 0:
                        continue

                    t = ((wx - x1) * (x2 - x1) + (wy - y1) * (y2 - y1)) / l2
                    t = max(0, min(1, t))
                    px_proj = x1 + t * (x2 - x1)
                    py_proj = y1 + t * (y2 - y1)

                    dist = math.sqrt((wx - px_proj) ** 2 + (wy - py_proj) ** 2)
                    if dist < 5 / self.app_state.zoom:
                        return shape

            elif isinstance(shape, Polygon):
                # Ray casting algorithm for point in polygon
                # https://en.wikipedia.org/wiki/Point_in_polygon
                n = len(shape.points)
                inside = False
                p1x, p1y = shape.points[0]
                for i in range(n + 1):
                    p2x, p2y = shape.points[i % n]
                    if wy > min(p1y, p2y):
                        if wy <= max(p1y, p2y):
                            if wx <= max(p1x, p2x):
                                if p1y != p2y:
                                    xinters = (wy - p1y) * (p2x - p1x) / (
                                        p2y - p1y
                                    ) + p1x
                                    if p1x == p2x or wx <= xinters:
                                        inside = not inside
                    p1x, p1y = p2x, p2y

                if inside:
                    return shape

        return None

    def on_pan_start(self, e: ft.DragStartEvent):
        wx, wy = self.to_world(e.local_x, e.local_y)
        self.last_wx = wx
        self.last_wy = wy

        if self.app_state.current_tool == ToolType.ERASER:
            hit_shape = self.hit_test(wx, wy)
            if hit_shape:
                if isinstance(hit_shape, Path):
                    # For Path, eraser drag interaction will be handled in on_pan_update.
                    # But if we just click, we might want to delete the whole path?
                    # "If the user selects the eraser and clicks on a shape it should be deleted."
                    # This implies full deletion on click.
                    # However, "If the user selects the eraser and drags over a path, delete the points that were touched."
                    # This implies partial deletion on drag.
                    # We can't know if it's a click or drag yet.
                    # But usually, instant action on pan_start feels responsive for "click".
                    # Let's defer full deletion to `on_pan_end` if no drag occurred?
                    # Or simpler:
                    # If we start on a shape that IS NOT a path, delete it immediately.
                    # If we start on a Path, we might be starting a drag erasure.
                    # Let's assume for non-Path shapes, we delete immediately.
                    if not isinstance(hit_shape, Path):
                        self.app_state.remove_shape(hit_shape)
                        return
                    else:
                        # It is a path. We start "erasing" points.
                        # We need to track that we are erasing this path.
                        self._erase_points_in_path(hit_shape, wx, wy)
                else:
                    self.app_state.remove_shape(hit_shape)
            return

        if self.app_state.current_tool == ToolType.HAND:
            self.start_pan_x = e.local_x
            self.start_pan_y = e.local_y
            self.initial_pan_x = self.app_state.pan_x
            self.initial_pan_y = self.app_state.pan_y

        elif self.app_state.current_tool == ToolType.BOX_SELECTION:
            # Check if we clicked on an existing selected shape.
            # If so, we want to MOVE, not start a new box selection.
            # UNLESS shift is held? Usually clicking a selected shape with shift might deselect it or just be ignored.
            # Standard: Click on selected -> Move. Click on empty/unselected -> New selection.

            hit_shape = self.hit_test(wx, wy)
            clicked_on_selected = (
                hit_shape and hit_shape.id in self.app_state.selected_shape_ids
            )

            if clicked_on_selected:
                # Switch to "move" mode (temporarily treat like SELECTION tool logic for moving)
                # We can just reuse the SELECTION tool logic block by calling it or copying it.
                # Let's copy the essential move initialization logic.
                self.drag_start_wx = wx
                self.drag_start_wy = wy
                self.moving_shapes_initial_state = {}
                for s in self.app_state.shapes:
                    if s.id in self.app_state.selected_shape_ids:
                        state = {"x": s.x, "y": s.y}
                        if isinstance(s, Line):
                            state.update({"end_x": s.end_x, "end_y": s.end_y})
                        elif isinstance(s, Polygon):
                            state.update({"points": list(s.points)})
                        self.moving_shapes_initial_state[s.id] = state

                # IMPORTANT: We are NOT starting a box selection.
                self.box_select_start_wx = None
                return

            # Start box selection (default behavior for empty space or unselected object)
            self.box_select_start_wx = wx
            self.box_select_start_wy = wy
            self.box_select_rect = (wx, wy, 0, 0)
            # Clear selection unless shift is held
            if not self.app_state.is_shift_down:
                self.app_state.select_shape(None)

        elif self.app_state.current_tool == ToolType.SELECTION:
            # Check for resize handles on selected shape first

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
                    handle = self.get_resize_handle(selected_shape, wx, wy)
                    if handle:
                        self.resize_handle = handle
                        self.resizing_shape = selected_shape
                        return

            hit_shape = self.hit_test(wx, wy)
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

                self.drag_start_wx = wx
                self.drag_start_wy = wy
                # Store initial positions for ALL selected shapes
                self.moving_shapes_initial_state = {}
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

                # Fallback to pan if background clicked? Or box select.
                # For now, let's allow pan if background clicked in selection mode
                self.start_pan_x = e.local_x
                self.start_pan_y = e.local_y
                self.initial_pan_x = self.app_state.pan_x
                self.initial_pan_y = self.app_state.pan_y

        elif self.app_state.current_tool == ToolType.LINE:
            color = (
                ft.Colors.WHITE
                if self.app_state.theme_mode == "dark"
                else ft.Colors.BLACK
            )

            # Check for start shape connection
            start_shape = self.hit_test(wx, wy)
            start_id = start_shape.id if start_shape else None
            start_anchor_id = None

            # Check for anchor snap on start
            if start_shape:
                threshold = 10 / self.app_state.zoom
                anchors = self.get_anchors(start_shape)
                for anchor_id, ax, ay in anchors:
                    if math.hypot(wx - ax, wy - ay) < threshold:
                        start_anchor_id = anchor_id
                        # Snap start point
                        wx, wy = ax, ay
                        break

            self.current_drawing_shape = Line(
                x=wx,
                y=wy,
                end_x=wx,
                end_y=wy,
                stroke_color=color,
                line_type=getattr(self.app_state, "selected_line_type", "simple"),
                start_shape_id=start_id,
                start_anchor_id=start_anchor_id,
            )
            self.app_state.add_shape(self.current_drawing_shape)

        elif self.app_state.current_tool == ToolType.RECTANGLE:
            color = (
                ft.Colors.WHITE
                if self.app_state.theme_mode == "dark"
                else ft.Colors.BLACK
            )
            self.current_drawing_shape = Rectangle(
                x=wx, y=wy, width=0, height=0, stroke_color=color
            )
            self.app_state.add_shape(self.current_drawing_shape)

        elif self.app_state.current_tool == ToolType.CIRCLE:
            color = (
                ft.Colors.WHITE
                if self.app_state.theme_mode == "dark"
                else ft.Colors.BLACK
            )
            # Initial click is the top-left corner (or anchor point)
            self.current_drawing_shape = Circle(
                x=wx, y=wy, radius_x=0, radius_y=0, stroke_color=color
            )
            self.app_state.add_shape(self.current_drawing_shape)

        elif self.app_state.current_tool == ToolType.POLYGON:
            color = (
                ft.Colors.WHITE
                if self.app_state.theme_mode == "dark"
                else ft.Colors.BLACK
            )
            # Create a Polygon with 0 size initially at click point.
            # Points will be generated in on_pan_update.
            # We store the center as the first point for now, or just empty?
            # Better to store initial center (wx, wy) in shape.x/y for reference during drag?
            # The Polygon shape class doesn't strictly use x/y for position (it uses points),
            # but we can use x/y as the "center" or "start anchor".
            # Let's use x,y as center.
            self.current_drawing_shape = Polygon(
                x=wx,
                y=wy,
                points=[],
                stroke_color=color,
                polygon_type=self.app_state.selected_polygon_type,
            )
            self.app_state.add_shape(self.current_drawing_shape)

        elif self.app_state.current_tool == ToolType.PEN:
            color = (
                ft.Colors.WHITE
                if self.app_state.theme_mode == "dark"
                else ft.Colors.BLACK
            )
            self.current_drawing_shape = Path(points=[(wx, wy)], stroke_color=color)
            self.app_state.add_shape(self.current_drawing_shape)

        elif self.app_state.current_tool == ToolType.TEXT:
            # Add text input field
            self._add_text_input(wx, wy)

    def on_pan_update(self, e: ft.DragUpdateEvent):
        wx, wy = self.to_world(e.local_x, e.local_y)
        # Capture previous last_wx before updating it?
        # Actually, self.last_wx is from the PREVIOUS call (or pan_start).
        # So we can calculate delta BEFORE updating self.last_wx.
        prev_wx = self.last_wx
        prev_wy = self.last_wy

        self.last_wx = wx
        self.last_wy = wy

        # Eraser dragging logic
        if self.app_state.current_tool == ToolType.ERASER:
            # Check if we hit any path while dragging
            # Note: The prompt says "drags over a path". This implies continuous hit testing.
            # But earlier we optimized by setting `current_drawing_shape` if we started on a path.
            # However, we might start on empty space and drag INTO a path.
            # So let's hit test continuously.

            hit_shape = self.hit_test(wx, wy)
            if hit_shape and isinstance(hit_shape, Path):
                self._erase_points_in_path(hit_shape, wx, wy)
            return

        # Special handling for HAND (pan) tool since it relies on screen coordinates delta
        if self.app_state.current_tool == ToolType.HAND:
            dx = e.local_x - self.start_pan_x
            dy = e.local_y - self.start_pan_y
            self.app_state.set_pan(self.initial_pan_x + dx, self.initial_pan_y + dy)
            return

        if self.app_state.current_tool == ToolType.BOX_SELECTION:
            if self.box_select_start_wx is not None:
                w = wx - self.box_select_start_wx
                h = wy - self.box_select_start_wy
                self.box_select_rect = (
                    self.box_select_start_wx,
                    self.box_select_start_wy,
                    w,
                    h,
                )
                self.app_state.notify()  # Trigger redraw to show box
                return

            # If we are NOT box selecting, but we have selected shapes, we might be moving them
            # (initiated in on_pan_start).
            # Fallthrough to update_active_interaction logic below.
            pass

        # Special handling for Selection Move (Pan) since it relies on screen/world deltas

        # Ideally we refactor this too, but for now let's keep it here or handle in update_active_interaction
        # Logic for selection move doesn't depend on shift key (yet), so it's less critical.
        # But to be clean, let's delegate.

        self.update_active_interaction(wx, wy, prev_wx, prev_wy)

    def _erase_points_in_path(self, path: Path, wx: float, wy: float):
        # Eraser radius in world coordinates
        eraser_radius = 10 / self.app_state.zoom

        # Find points to remove
        # We need to preserve the order and split if necessary.
        # "If the points in a path are in the middle, turn the path into two separate path items."

        new_points_list = []
        current_segment = []

        points_removed = False

        for i, (px, py) in enumerate(path.points):
            dist = math.hypot(px - wx, py - wy)
            is_erased = dist < eraser_radius
            if is_erased:
                # Point is erased.
                points_removed = True
                if current_segment:
                    new_points_list.append(current_segment)
                    current_segment = []
            else:
                current_segment.append((px, py))

        if current_segment:
            new_points_list.append(current_segment)

        if not points_removed:
            return

        # If we removed all points, delete the shape
        if not new_points_list:
            self.app_state.remove_shape(path)
            return

        # If we have 1 segment, just update the path
        if len(new_points_list) == 1:
            path.points = new_points_list[0]
            # If a path has too few points (e.g. 0 or 1), maybe delete it?
            # Pen usually needs 2 points to be visible unless it's a dot.
            if len(path.points) < 1:
                self.app_state.remove_shape(path)
            else:
                self.app_state.update_shape(path)
        else:
            # We have multiple segments.
            # Update the original path to be the first segment
            # Create new paths for the rest

            # First segment
            first_seg = new_points_list[0]
            path.points = first_seg
            if len(path.points) < 1:
                # If first segment is empty (shouldn't happen with logic above) or too small
                # Actually logic above ensures non-empty segments are added.
                pass
            self.app_state.update_shape(path)

            # Create new paths for subsequent segments
            for segment in new_points_list[1:]:
                if len(segment) >= 1:
                    new_path = Path(
                        points=segment,
                        stroke_color=path.stroke_color,
                        stroke_width=path.stroke_width,
                        filled=path.filled,
                        fill_color=path.fill_color,
                    )
                    self.app_state.add_shape(new_path)

            # Ensure the state is saved/notified after all changes
            # add_shape calls notify(save=True) internally, so we are good for new shapes.
            # but update_shape calls notify(save=True) too.
            # This is fine.

    def _generate_polygon_points(self, cx, cy, rx, ry, poly_type):
        points = []

        if poly_type == "triangle":
            sides = 3
            # Point up
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

    def _add_text_input(self, wx, wy):
        # Convert world to screen for UI placement (center of screen for dialog?)
        # Or we can open a Dialog.
        # Flet Dialogs are overlayed on the page.

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

        # We need access to page to open dialog
        # Since this is a Control, we have self.page if mounted.
        if self.page:
            self.page.open(dlg)
            self.page.update()

    def update_active_interaction(self, wx, wy, prev_wx=None, prev_wy=None):
        if getattr(self, "_is_updating_interaction", False):
            return
        self._is_updating_interaction = True
        try:
            self._update_active_interaction_internal(wx, wy, prev_wx, prev_wy)
        finally:
            self._is_updating_interaction = False

    def _update_active_interaction_internal(self, wx, wy, prev_wx=None, prev_wy=None):
        if self.app_state.current_tool in (ToolType.SELECTION, ToolType.BOX_SELECTION):
            if self.resizing_shape:
                # Handle resizing
                shape = self.resizing_shape

                if isinstance(shape, Line):
                    if self.resize_handle == "start":
                        shape.x = wx
                        shape.y = wy
                    elif self.resize_handle == "end":
                        shape.end_x = wx
                        shape.end_y = wy

                elif isinstance(shape, Rectangle):
                    # For Rectangle, dragging a handle means updating one corner
                    # while keeping the opposite corner fixed.

                    # Current absolute corners
                    x1 = shape.x
                    y1 = shape.y
                    x2 = shape.x + shape.width
                    y2 = shape.y + shape.height

                    # Update the corner corresponding to the handle
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
                    # Similar to rectangle
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
                    # Resize polygon via bounding box
                    xs = [p[0] for p in shape.points]
                    ys = [p[1] for p in shape.points]
                    min_x, max_x = min(xs), max(xs)
                    min_y, max_y = min(ys), max(ys)

                    # Current bounding box
                    old_w = max_x - min_x
                    old_h = max_y - min_y
                    old_cx = min_x + old_w / 2
                    old_cy = min_y + old_h / 2

                    # New bounding box coords
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

                    # New dimensions
                    new_w = nx2 - nx1
                    new_h = ny2 - ny1

                    # Avoid zero division
                    if old_w == 0:
                        old_w = 0.001
                    if old_h == 0:
                        old_h = 0.001

                    scale_x = new_w / old_w
                    scale_y = new_h / old_h

                    # Center of new bounding box
                    new_cx = nx1 + new_w / 2
                    new_cy = ny1 + new_h / 2

                    # Transform all points
                    new_points = []
                    for px, py in shape.points:
                        # Normalize to center
                        dx = px - old_cx
                        dy = py - old_cy

                        # Scale
                        dx *= scale_x
                        dy *= scale_y

                        # Translate to new center
                        new_px = new_cx + dx
                        new_py = new_cy + dy
                        new_points.append((new_px, new_py))

                    shape.points = new_points
                    # Update anchor x/y just in case
                    shape.x = nx1
                    shape.y = ny1

                self.app_state.update_shape(shape)
                return

            if self.app_state.selected_shape_ids:
                # Move object
                # Calculate frame delta
                if prev_wx is not None and prev_wy is not None:
                    dx = wx - prev_wx
                    dy = wy - prev_wy
                else:
                    dx = 0
                    dy = 0

                if dx == 0 and dy == 0:
                    return

                # Move all selected shapes
                # Create a copy to avoid issues if set changes during iteration (though unexpected)
                # But we have recursive updates which might modify other shapes.
                # Crucial: update_shape_position already triggers recursion.
                # If multiple connected shapes are selected, we might move them twice!
                # E.g. A and B are selected. B is attached to A.
                # Move A -> updates A -> recursively updates B.
                # Then Move B -> updates B again!

                # To prevent double-moving, we should perhaps only move "independent" shapes in the selection?
                # Or, update_shape_position needs to know it's part of a batch move.

                # Simple fix: Pass the set of selected IDs to update_shape_position or a helper,
                # and in the recursion, if a shape is ALSO in the selection set, DO NOT move it recursively
                # (because it will be moved by the main loop).

                # Actually, our current recursion in AppState `_update_connected_lines` checks:
                # `if s.id in self.app_state.selected_shape_ids: continue`
                # This PREVENTS recursive updates for selected shapes.
                # So if A and B are selected, moving A will NOT update B recursively.
                # Moving B (in the loop) will move B.
                # This seems correct for rigid moves of a group.

                for shape in self.app_state.shapes:
                    if shape.id in self.app_state.selected_shape_ids:
                        self.app_state.update_shape_position(shape, dx, dy, save=False)

                # Notify once at the end (or continuously for drag)
                self.app_state.notify(save=False)  # Don't save on every drag step

            else:
                # Pan logic handled in on_pan_update
                pass

        elif self.current_drawing_shape:
            if isinstance(self.current_drawing_shape, Line):
                dx = wx - self.current_drawing_shape.x
                dy = wy - self.current_drawing_shape.y

                if self.app_state.is_shift_down:
                    # Snap to 45 degree increments
                    angle = math.atan2(dy, dx)
                    snap_angle = round(angle / (math.pi / 4)) * (math.pi / 4)
                    length = math.sqrt(dx * dx + dy * dy)

                    self.current_drawing_shape.end_x = (
                        self.current_drawing_shape.x + length * math.cos(snap_angle)
                    )
                    self.current_drawing_shape.end_y = (
                        self.current_drawing_shape.y + length * math.sin(snap_angle)
                    )
                else:
                    self.current_drawing_shape.end_x = wx
                    self.current_drawing_shape.end_y = wy

            elif isinstance(self.current_drawing_shape, Rectangle):
                current_w = wx - self.current_drawing_shape.x
                current_h = wy - self.current_drawing_shape.y

                if self.app_state.is_shift_down:
                    # Force square, using the larger dimension
                    max_dim = max(abs(current_w), abs(current_h))
                    # Preserve direction
                    current_w = max_dim if current_w >= 0 else -max_dim
                    current_h = max_dim if current_h >= 0 else -max_dim

                self.current_drawing_shape.width = current_w
                self.current_drawing_shape.height = current_h

            elif isinstance(self.current_drawing_shape, Circle):
                # User drags to define the opposite corner of the bounding box.
                # Start point: self.start_pan_x, self.start_pan_y (Screen coords)
                # But here we are in on_pan_update, and we have wx, wy (current World coords).
                # We need the START point in World coords.
                # Unlike PAN tool, we didn't save start_wx/start_wy specifically for drawing tools in `on_pan_start`.
                # But for `Circle`, `x` and `y` were initialized to `wx`, `wy` at start.

                # So current_drawing_shape.x / y is the anchor point (start).
                start_x = self.current_drawing_shape.x
                start_y = self.current_drawing_shape.y

                # Update shape to represent the NEW top-left and size
                rx = (wx - start_x) / 2
                ry = (wy - start_y) / 2

                # Constrain to perfect circle if shift is held
                if self.app_state.is_shift_down:
                    # Use the larger dimension? Or just sync them?
                    # Typical UX: max of abs(rx), abs(ry), preserving sign if possible?
                    # Usually drag direction determines sign.
                    # Let's take the max dimension.
                    max_r = max(abs(rx), abs(ry))

                    # Preserve sign of drag
                    rx = max_r if rx >= 0 else -max_r
                    ry = max_r if ry >= 0 else -max_r

                self.current_drawing_shape.radius_x = rx
                self.current_drawing_shape.radius_y = ry

            elif isinstance(self.current_drawing_shape, Polygon):
                # Anchor is center? Or TL?
                # Let's assume click was CENTER.
                cx = self.current_drawing_shape.x
                cy = self.current_drawing_shape.y

                rx = abs(wx - cx)
                ry = abs(wy - cy)

                if self.app_state.is_shift_down:
                    r = max(rx, ry)
                    rx = r
                    ry = r

                points = self._generate_polygon_points(
                    cx, cy, rx, ry, self.current_drawing_shape.polygon_type
                )
                self.current_drawing_shape.points = points

            elif isinstance(self.current_drawing_shape, Path):
                if (
                    not self.current_drawing_shape.points
                    or self.current_drawing_shape.points[-1] != (wx, wy)
                ):
                    self.current_drawing_shape.points.append((wx, wy))

            self.app_state.notify()

    def on_pan_end(self, e: ft.DragEndEvent):
        # Finalize connection if line tool
        if self.app_state.current_tool == ToolType.LINE and isinstance(
            self.current_drawing_shape, Line
        ):
            # Check for end shape connection
            # Use last world coordinates from pan_update (self.last_wx, self.last_wy)
            # But we should ignore the line itself being drawn
            wx, wy = self.last_wx, self.last_wy

            end_shape = self.hit_test(
                wx, wy, exclude_ids={self.current_drawing_shape.id}
            )

            if end_shape:
                self.current_drawing_shape.end_shape_id = end_shape.id

                # Check for anchor snap on end
                threshold = 10 / self.app_state.zoom
                anchors = self.get_anchors(end_shape)
                for anchor_id, ax, ay in anchors:
                    if math.hypot(wx - ax, wy - ay) < threshold:
                        self.current_drawing_shape.end_anchor_id = anchor_id
                        # Snap end point
                        self.current_drawing_shape.end_x = ax
                        self.current_drawing_shape.end_y = ay
                        break

        self.app_state.notify()

        if self.app_state.current_tool == ToolType.BOX_SELECTION:
            if self.box_select_start_wx is not None:
                if self.box_select_rect:
                    # Find shapes inside rect
                    x, y, w, h = self.box_select_rect
                    # Normalize rect
                    if w < 0:
                        x += w
                        w = abs(w)
                    if h < 0:
                        y += h
                        h = abs(h)

                    found_ids = []
                    for shape in self.app_state.shapes:
                        if self._is_shape_in_rect(shape, x, y, w, h):
                            found_ids.append(shape.id)

                    # Logic for shift key (add to selection)
                    if self.app_state.is_shift_down:
                        current = list(self.app_state.selected_shape_ids)
                        # Add unique new ones
                        for fid in found_ids:
                            if fid not in current:
                                current.append(fid)
                        self.app_state.select_shapes(current)
                    else:
                        self.app_state.select_shapes(found_ids)

                self.box_select_rect = None
                self.box_select_start_wx = None
                self.box_select_start_wy = None
                # Switch back to normal selection? Or keep tool active?
                # Standard behavior: keep tool active for another box select.
                # User can switch to object selection manually.
                self.app_state.notify()  # Clear the box

        self.current_drawing_shape = None

        self.resize_handle = None
        self.resizing_shape = None

        # Reset shift key state on drag end to prevent stuck keys
        self.app_state.set_shift_key(False)

    def _is_shape_in_rect(self, shape, rx, ry, rw, rh):
        # Helper to check if shape is strictly inside rect (or intersects?)
        # "select all objects within the box" usually means fully contained or intersecting.
        # Common behavior: Intersecting.
        # Let's start with a simple bounding box intersection check.

        # Get bounding box of shape
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

        # Check intersection
        return sx < rx + rw and sx + sw > rx and sy < ry + rh and sy + sh > ry

    def on_hover(self, e: ft.HoverEvent):
        # Update hover coordinates
        # Note: e.local_x/y might need to be converted to world
        # Flet HoverEvent has global_x, global_y, local_x, local_y
        self.hover_wx, self.hover_wy = self.to_world(e.local_x, e.local_y)

        # Trigger redraw to show anchors if line tool is active
        if self.app_state.current_tool == ToolType.LINE:
            self.app_state.notify()

    def on_scroll(self, e: ft.ScrollEvent):
        if e.scroll_delta_y is None:
            return

        zoom_factor = 1.1 if e.scroll_delta_y < 0 else 0.9
        old_zoom = self.app_state.zoom
        new_zoom = max(0.1, min(10.0, old_zoom * zoom_factor))

        wx, wy = self.to_world(e.local_x, e.local_y)
        self.app_state.set_zoom(new_zoom)

        new_sx = (wx * new_zoom) + self.app_state.pan_x
        new_sy = (wy * new_zoom) + self.app_state.pan_y
        self.app_state.set_pan(
            self.app_state.pan_x + (e.local_x - new_sx),
            self.app_state.pan_y + (e.local_y - new_sy),
        )
