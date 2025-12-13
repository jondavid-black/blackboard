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
            elif isinstance(shape, Rectangle):
                sx, sy = self.to_screen(shape.x, shape.y)
                w = shape.width * self.app_state.zoom
                h = shape.height * self.app_state.zoom
                canvas_shapes.append(cv.Rect(sx, sy, w, h, paint=paint))
            elif isinstance(shape, Circle):
                sx, sy = self.to_screen(shape.x, shape.y)
                r = shape.radius * self.app_state.zoom
                canvas_shapes.append(cv.Circle(sx, sy, r, paint=paint))
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
                dx = wx - shape.x
                dy = wy - shape.y
                if math.sqrt(dx * dx + dy * dy) <= shape.radius:
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
        return None

    def on_pan_start(self, e: ft.DragStartEvent):
        wx, wy = self.to_world(e.local_x, e.local_y)

        if self.app_state.current_tool == ToolType.HAND:
            self.start_pan_x = e.local_x
            self.start_pan_y = e.local_y
            self.initial_pan_x = self.app_state.pan_x
            self.initial_pan_y = self.app_state.pan_y

        elif self.app_state.current_tool == ToolType.SELECTION:
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
            self.current_drawing_shape = Circle(
                x=wx, y=wy, radius=0, stroke_color=color
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

        if self.app_state.current_tool == ToolType.HAND:
            dx = e.local_x - self.start_pan_x
            dy = e.local_y - self.start_pan_y
            self.app_state.set_pan(self.initial_pan_x + dx, self.initial_pan_y + dy)

        elif self.app_state.current_tool == ToolType.SELECTION:
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
                # Pan
                dx = e.local_x - self.start_pan_x
                dy = e.local_y - self.start_pan_y
                self.app_state.set_pan(self.initial_pan_x + dx, self.initial_pan_y + dy)

        elif self.current_drawing_shape:
            if isinstance(self.current_drawing_shape, Line):
                self.current_drawing_shape.end_x = wx
                self.current_drawing_shape.end_y = wy

            elif isinstance(self.current_drawing_shape, Rectangle):
                self.current_drawing_shape.width = wx - self.current_drawing_shape.x
                self.current_drawing_shape.height = wy - self.current_drawing_shape.y

            elif isinstance(self.current_drawing_shape, Circle):
                dx = wx - self.current_drawing_shape.x
                dy = wy - self.current_drawing_shape.y
                self.current_drawing_shape.radius = math.sqrt(dx * dx + dy * dy)

            elif isinstance(self.current_drawing_shape, Path):
                self.current_drawing_shape.points.append((wx, wy))

            self.app_state.notify()

    def on_pan_end(self, e: ft.DragEndEvent):
        self.current_drawing_shape = None

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
