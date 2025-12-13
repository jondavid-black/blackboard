import flet as ft
import flet.canvas as cv
import math
from ..state.app_state import AppState
from ..models import ToolType, Shape, Line, Rectangle, Circle, Text, Path


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
        self.resize_handle = None
        self.resizing_shape = None

        # Track last world coordinates for refreshing logic when modifier keys change
        self.last_wx = 0
        self.last_wy = 0

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

            if self.app_state.selected_shape_id == shape.id:
                paint.color = ft.Colors.BLUE
                paint.stroke_width = shape.stroke_width + 2

            if isinstance(shape, Line):
                sx1, sy1 = self.to_screen(shape.x, shape.y)
                sx2, sy2 = self.to_screen(shape.end_x, shape.end_y)
                canvas_shapes.append(cv.Line(sx1, sy1, sx2, sy2, paint=paint))

                # Draw handles if selected
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

                # Draw handles if selected
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
                if self.app_state.selected_shape_id == shape.id:
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

        return None

    def hit_test(self, wx, wy):
        # Simple hit test
        for shape in reversed(self.app_state.shapes):
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

        return None

    def on_pan_start(self, e: ft.DragStartEvent):
        wx, wy = self.to_world(e.local_x, e.local_y)

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
                        self.current_drawing_shape = (
                            hit_shape  # Reusing this to track active shape
                        )
                        self._erase_points_in_path(hit_shape, wx, wy)
                else:
                    self.app_state.remove_shape(hit_shape)
            return

        if self.app_state.current_tool == ToolType.HAND:
            self.start_pan_x = e.local_x
            self.start_pan_y = e.local_y
            self.initial_pan_x = self.app_state.pan_x
            self.initial_pan_y = self.app_state.pan_y

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
                self.app_state.select_shape(hit_shape.id)
                self.drag_start_wx = wx
                self.drag_start_wy = wy
                self.moving_shape_initial_x = hit_shape.x
                self.moving_shape_initial_y = hit_shape.y
                if isinstance(hit_shape, Line):
                    self.moving_shape_initial_end_x = hit_shape.end_x
                    self.moving_shape_initial_end_y = hit_shape.end_y
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
            self.current_drawing_shape = Line(
                x=wx, y=wy, end_x=wx, end_y=wy, stroke_color=color
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

        elif self.app_state.current_tool == ToolType.PEN:
            color = (
                ft.Colors.WHITE
                if self.app_state.theme_mode == "dark"
                else ft.Colors.BLACK
            )
            self.current_drawing_shape = Path(points=[(wx, wy)], stroke_color=color)
            self.app_state.add_shape(self.current_drawing_shape)

        elif self.app_state.current_tool == ToolType.TEXT:
            # For prototype, just add text. In real app, show input.
            color = (
                ft.Colors.WHITE
                if self.app_state.theme_mode == "dark"
                else ft.Colors.BLACK
            )
            self.app_state.add_shape(
                Text(x=wx, y=wy, content="Hello World", stroke_color=color)
            )
            self.app_state.set_tool(
                ToolType.SELECTION
            )  # Switch back to selection after placing text

    def on_pan_update(self, e: ft.DragUpdateEvent):
        wx, wy = self.to_world(e.local_x, e.local_y)
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

        # Special handling for Selection Move (Pan) since it relies on screen/world deltas
        # Ideally we refactor this too, but for now let's keep it here or handle in update_active_interaction
        # Logic for selection move doesn't depend on shift key (yet), so it's less critical.
        # But to be clean, let's delegate.

        self.update_active_interaction(wx, wy)

    def _erase_points_in_path(self, path: Path, wx: float, wy: float):
        # Eraser radius in world coordinates
        eraser_radius = 10 / self.app_state.zoom

        # Find points to remove
        # We need to preserve the order and split if necessary.
        # "If the points in a path are in the middle, turn the path into two separate path items."

        new_points_list = []
        current_segment = []

        points_removed = False

        for px, py in path.points:
            if math.hypot(px - wx, py - wy) < eraser_radius:
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

    def update_active_interaction(self, wx, wy):
        if getattr(self, "_is_updating_interaction", False):
            return
        self._is_updating_interaction = True
        try:
            self._update_active_interaction_internal(wx, wy)
        finally:
            self._is_updating_interaction = False

    def _update_active_interaction_internal(self, wx, wy):
        if self.app_state.current_tool == ToolType.SELECTION:
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

                self.app_state.notify()
                return

            if self.app_state.selected_shape_id:
                # Move object
                dx = wx - self.drag_start_wx
                dy = wy - self.drag_start_wy

                # Find shape
                shape = next(
                    (
                        s
                        for s in self.app_state.shapes
                        if s.id == self.app_state.selected_shape_id
                    ),
                    None,
                )
                if shape:
                    shape.x = self.moving_shape_initial_x + dx
                    shape.y = self.moving_shape_initial_y + dy
                    if isinstance(shape, Line):
                        shape.end_x = self.moving_shape_initial_end_x + dx
                        shape.end_y = self.moving_shape_initial_end_y + dy
                    self.app_state.notify()
            else:
                # Pan logic handled in on_pan_update for now or here?
                # e.local_x is not available here.
                # So we leave Selection Pan (background drag) in on_pan_update if possible,
                # but wait, on_pan_update called this.
                # If we are in Selection mode and NO shape is selected, we are panning.
                # But panning needs `e.local_x`.
                # Let's handle panning in `on_pan_update` explicitly before calling this.
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

            elif isinstance(self.current_drawing_shape, Path):
                self.current_drawing_shape.points.append((wx, wy))

            self.app_state.notify()

    def on_pan_end(self, e: ft.DragEndEvent):
        self.current_drawing_shape = None
        self.resize_handle = None
        self.resizing_shape = None

        # Reset shift key state on drag end to prevent stuck keys
        self.app_state.set_shift_key(False)

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
