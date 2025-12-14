import flet as ft
import flet.canvas as cv
import flet.core.painting as painting
import math
from ..state.app_state import AppState
from ..models import (
    ToolType,
    Shape,
    Line,
    Rectangle,
    Circle,
    Text,
    Path,
    Polygon,
    Group,
)
from .tools.line_tool import LineTool
from .tools.rectangle_tool import RectangleTool
from .tools.circle_tool import CircleTool
from .tools.text_tool import TextTool
from .tools.polygon_tool import PolygonTool
from .tools.pen_tool import PenTool
from .tools.eraser_tool import EraserTool
from .tools.selection_tool import SelectionTool
from .tools.hand_tool import HandTool
from .tools.box_selection_tool import BoxSelectionTool


class BlackboardCanvas(cv.Canvas):
    def __init__(self, app_state: AppState):
        self.app_state = app_state
        self.tools = {
            ToolType.LINE: LineTool(self),
            ToolType.RECTANGLE: RectangleTool(self),
            ToolType.CIRCLE: CircleTool(self),
            ToolType.TEXT: TextTool(self),
            ToolType.POLYGON: PolygonTool(self),
            ToolType.PEN: PenTool(self),
            ToolType.ERASER: EraserTool(self),
            ToolType.SELECTION: SelectionTool(self),
            ToolType.HAND: HandTool(self),
            ToolType.BOX_SELECTION: BoxSelectionTool(self),
        }

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

        # Track last world coordinates
        self.last_wx = 0
        self.last_wy = 0
        self.hover_wx = 0
        self.hover_wy = 0

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

    def _on_state_change(self):
        if self._is_updating_interaction:
            return

        # If we have an active drawing tool and shape, update its geometry based on current modifiers
        if self.current_drawing_shape:
            self._is_updating_interaction = True
            try:
                tool = self.tools.get(self.app_state.current_tool)
                if tool:
                    # Re-apply the move logic with the last known coordinates to respect new modifier state
                    tool.on_move(self.last_wx, self.last_wy, None)
            finally:
                self._is_updating_interaction = False

        # Update canvas background based on theme
        # (Transparent to allow background component to show)
        self.gesture_container.bgcolor = ft.Colors.TRANSPARENT

        canvas_shapes = []
        overlay_shapes = []

        default_stroke_color = (
            ft.Colors.WHITE if self.app_state.theme_mode == "dark" else ft.Colors.BLACK
        )

        # 1. Draw all shapes
        for shape in self.app_state.shapes:
            # Theme adaptation for colors
            stroke_color = (
                shape.stroke_color if shape.stroke_color else default_stroke_color
            )
            final_color = stroke_color
            if self.app_state.theme_mode == "dark" and stroke_color == ft.Colors.BLACK:
                final_color = ft.Colors.WHITE
            elif (
                self.app_state.theme_mode == "light" and stroke_color == ft.Colors.WHITE
            ):
                final_color = ft.Colors.BLACK

            if not final_color:
                final_color = default_stroke_color

            stroke_join = getattr(shape, "stroke_join", "miter")
            stroke_join_enum = painting.StrokeJoin.MITER
            stroke_cap_enum = ft.StrokeCap.BUTT
            if stroke_join == "round":
                stroke_join_enum = painting.StrokeJoin.ROUND
                stroke_cap_enum = ft.StrokeCap.ROUND
            elif stroke_join == "bevel":
                stroke_join_enum = painting.StrokeJoin.BEVEL
                stroke_cap_enum = ft.StrokeCap.SQUARE  # Just to have a different cap

            # Explicitly type cast or use values if enum matching is weird in Pylance/Runtime
            # But based on checks, they are correct.
            # Let's try to ensure we are using the one from the Paint signature if possible,
            # or just rely on the fact that flet exports them correctly.

            paint = self._create_paint(shape, final_color)

            # Highlight selected
            if (
                self.app_state.selected_shape_id == shape.id
                or shape.id in self.app_state.selected_shape_ids
            ):
                paint.color = ft.Colors.BLUE
                if self.app_state.is_shift_down:
                    paint.color = ft.Colors.CYAN
                paint.stroke_width = shape.stroke_width + 2
                # Selection highlight ignores dash array for visibility
                paint.stroke_dash_pattern = None

            if isinstance(shape, Group):
                # Draw children
                for child in shape.children:
                    # Determine paint for child
                    child_stroke_color = (
                        child.stroke_color
                        if child.stroke_color
                        else default_stroke_color
                    )
                    child_final_color = child_stroke_color
                    if (
                        self.app_state.theme_mode == "dark"
                        and child_stroke_color == ft.Colors.BLACK
                    ):
                        child_final_color = ft.Colors.WHITE
                    elif (
                        self.app_state.theme_mode == "light"
                        and child_stroke_color == ft.Colors.WHITE
                    ):
                        child_final_color = ft.Colors.BLACK

                    if not child_final_color:
                        child_final_color = default_stroke_color

                    child_paint = self._create_paint(child, child_final_color)

                    # Draw the child
                    self._draw_shape(
                        canvas_shapes, child, child_paint, child_final_color
                    )
            else:
                self._draw_shape(canvas_shapes, shape, paint, final_color)

        # 2. Delegate overlay drawing to current tool
        current_tool = self.tools.get(self.app_state.current_tool)
        if current_tool:
            current_tool.draw_overlays(overlay_shapes)

        self.shapes = canvas_shapes + overlay_shapes
        self.update()

    def _create_paint(self, shape, color):
        stroke_join = getattr(shape, "stroke_join", "miter")
        stroke_join_enum = painting.StrokeJoin.MITER
        stroke_cap_enum = ft.StrokeCap.BUTT
        if stroke_join == "round":
            stroke_join_enum = painting.StrokeJoin.ROUND
            stroke_cap_enum = ft.StrokeCap.ROUND
        elif stroke_join == "bevel":
            stroke_join_enum = painting.StrokeJoin.BEVEL
            stroke_cap_enum = ft.StrokeCap.SQUARE

        paint = ft.Paint(
            color=color,
            stroke_width=shape.stroke_width,
            style=ft.PaintingStyle.STROKE,
            stroke_dash_pattern=shape.stroke_dash_array,
            stroke_join=stroke_join_enum,
            stroke_cap=stroke_cap_enum,
        )

        if hasattr(shape, "opacity") and shape.opacity < 1.0:
            paint.color = ft.Colors.with_opacity(shape.opacity, color)

        return paint

    def _draw_shape(self, canvas_shapes, shape, paint, final_color):
        # Handle Fill
        fill_paint = None
        if shape.filled and shape.fill_color:
            fill_color = shape.fill_color
            if hasattr(shape, "opacity") and shape.opacity < 1.0:
                fill_color = ft.Colors.with_opacity(shape.opacity, fill_color)

            fill_paint = ft.Paint(color=fill_color, style=ft.PaintingStyle.FILL)

        if isinstance(shape, Line):
            sx1, sy1 = self.to_screen(shape.x, shape.y)
            sx2, sy2 = self.to_screen(shape.end_x, shape.end_y)

            line_type = getattr(shape, "line_type", "simple")

            if line_type == "angle_connector":
                mid_x = (sx1 + sx2) / 2
                canvas_shapes.append(cv.Line(sx1, sy1, mid_x, sy1, paint=paint))
                canvas_shapes.append(cv.Line(mid_x, sy1, mid_x, sy2, paint=paint))
                canvas_shapes.append(cv.Line(mid_x, sy2, sx2, sy2, paint=paint))
            else:
                canvas_shapes.append(cv.Line(sx1, sy1, sx2, sy2, paint=paint))

                if line_type == "arrow":
                    self._draw_arrow_head(canvas_shapes, sx1, sy1, sx2, sy2, paint)

        elif isinstance(shape, Rectangle):
            sx, sy = self.to_screen(shape.x, shape.y)
            w = shape.width * self.app_state.zoom
            h = shape.height * self.app_state.zoom

            # Construct a Path for the rectangle to ensure stroke_join (corner style) works consistently
            # IMPORTANT: For stroke_join to work, it must be a single continuous Path, not cv.Rect
            path_elements = [
                cv.Path.MoveTo(sx, sy),
                cv.Path.LineTo(sx + w, sy),
                cv.Path.LineTo(sx + w, sy + h),
                cv.Path.LineTo(sx, sy + h),
                cv.Path.Close(),
            ]

            if fill_paint:
                canvas_shapes.append(
                    cv.Path(
                        elements=path_elements,
                        paint=fill_paint,
                    )
                )

            canvas_shapes.append(
                cv.Path(
                    elements=path_elements,
                    paint=paint,
                )
            )

        elif isinstance(shape, Circle):
            sx, sy = self.to_screen(shape.x, shape.y)
            w = shape.radius_x * 2 * self.app_state.zoom
            h = shape.radius_y * 2 * self.app_state.zoom
            if fill_paint:
                canvas_shapes.append(cv.Oval(sx, sy, w, h, paint=fill_paint))
            canvas_shapes.append(cv.Oval(sx, sy, w, h, paint=paint))

        elif isinstance(shape, Text):
            sx, sy = self.to_screen(shape.x, shape.y)
            text_color = final_color
            if hasattr(shape, "opacity") and shape.opacity < 1.0:
                text_color = ft.Colors.with_opacity(shape.opacity, text_color)

            canvas_shapes.append(
                cv.Text(
                    sx,
                    sy,
                    shape.content,
                    style=ft.TextStyle(
                        size=shape.font_size * self.app_state.zoom,
                        color=text_color,
                    ),
                )
            )

        elif isinstance(shape, Path):
            if not shape.points:
                return
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
                return

            screen_points = [self.to_screen(px, py) for px, py in shape.points]
            if not screen_points:
                return

            path_elements = []
            path_elements.append(
                cv.Path.MoveTo(screen_points[0][0], screen_points[0][1])
            )
            for x, y in screen_points[1:]:
                path_elements.append(cv.Path.LineTo(x, y))
            path_elements.append(cv.Path.Close())

            if fill_paint:
                canvas_shapes.append(
                    cv.Path(
                        elements=path_elements,
                        paint=fill_paint,
                    )
                )

            canvas_shapes.append(
                cv.Path(
                    elements=path_elements,
                    paint=paint,
                )
            )

    def _draw_arrow_head(self, canvas_shapes, sx1, sy1, sx2, sy2, paint):
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

    def hit_test(self, wx, wy, exclude_ids=None):
        if exclude_ids is None:
            exclude_ids = set()
        else:
            exclude_ids = set(exclude_ids)

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
                rx = shape.radius_x
                ry = shape.radius_y
                if rx == 0 or ry == 0:
                    continue
                cx = shape.x + rx
                cy = shape.y + ry
                dx = wx - cx
                dy = wy - cy
                if (dx * dx) / (rx * rx) + (dy * dy) / (ry * ry) <= 1:
                    return shape
            elif isinstance(shape, Line):
                x1, y1 = shape.x, shape.y
                x2, y2 = shape.end_x, shape.end_y
                l2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
                if l2 == 0:
                    if math.sqrt((wx - x1) ** 2 + (wy - y1) ** 2) < 5:
                        return shape
                    continue
                t = ((wx - x1) * (x2 - x1) + (wy - y1) * (y2 - y1)) / l2
                t = max(0, min(1, t))
                px = x1 + t * (x2 - x1)
                py = y1 + t * (y2 - y1)
                if math.sqrt((wx - px) ** 2 + (wy - py) ** 2) < 5 / self.app_state.zoom:
                    return shape
            elif isinstance(shape, Text):
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
                threshold = 10 / self.app_state.zoom
                # Check points
                for px, py in shape.points:
                    if math.hypot(wx - px, wy - py) < threshold:
                        return shape
                # Check segments
                for i in range(len(shape.points) - 1):
                    p1 = shape.points[i]
                    p2 = shape.points[i + 1]
                    x1, y1 = p1
                    x2, y2 = p2
                    l2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
                    if l2 == 0:
                        continue
                    t = ((wx - x1) * (x2 - x1) + (wy - y1) * (y2 - y1)) / l2
                    t = max(0, min(1, t))
                    px_proj = x1 + t * (x2 - x1)
                    py_proj = y1 + t * (y2 - y1)
                    if (
                        math.sqrt((wx - px_proj) ** 2 + (wy - py_proj) ** 2)
                        < 5 / self.app_state.zoom
                    ):
                        return shape
            elif isinstance(shape, Polygon):
                # Point in polygon
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
            elif isinstance(shape, Group):
                # Check children. If we hit a child, we return the GROUP.
                # Because selection should select the group, not the child.
                # BUT, we might want to support deep selection later (e.g. ctrl+click).
                # For now, standard behavior: click child -> select group.

                # We need to use hit_test logic recursively but we can't easily call self.hit_test
                # because we need to check against children list, not app_state.shapes.

                # Simple recursion helper
                for child in reversed(shape.children):
                    # We can reuse the logic by temporarily mocking app_state.shapes? No that's messy.
                    # Ideally we refactor hit_test to take a list of shapes.
                    # For now, let's just duplicate the logic check or extract it.
                    # Or, better: Refactor hit_test to accept a list of shapes to test against.
                    pass

                # Since we haven't refactored hit_test yet, let's do a quick hack:
                # Iterate children and assume standard hit testing rules.
                # But wait, Group children are standard shapes.
                # So we can extract the hit test logic into a static method or helper?

                # Let's refactor hit_test to accept a list of shapes!
                pass

        return None

    def _hit_test_shapes(self, shapes, wx, wy):
        """Helper to hit test a specific list of shapes."""
        for shape in reversed(shapes):
            if isinstance(shape, Group):
                if self._hit_test_shapes(shape.children, wx, wy):
                    return shape

            # ... existing logic ...
            # This is getting complex to copy-paste.
            # Let's assume for now we just want to know if *any* child is hit.
            # If so, return the group.

            hit = self._is_point_in_shape(shape, wx, wy)
            if hit:
                return shape
        return None

    def _is_point_in_shape(self, shape, wx, wy):
        if isinstance(shape, Rectangle):
            return (
                shape.x <= wx <= shape.x + shape.width
                and shape.y <= wy <= shape.y + shape.height
            )
        elif isinstance(shape, Circle):
            rx = shape.radius_x
            ry = shape.radius_y
            if rx == 0 or ry == 0:
                return False
            cx = shape.x + rx
            cy = shape.y + ry
            dx = wx - cx
            dy = wy - cy
            return (dx * dx) / (rx * rx) + (dy * dy) / (ry * ry) <= 1
        elif isinstance(shape, Line):
            x1, y1 = shape.x, shape.y
            x2, y2 = shape.end_x, shape.end_y
            l2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
            if l2 == 0:
                return math.sqrt((wx - x1) ** 2 + (wy - y1) ** 2) < 5
            t = ((wx - x1) * (x2 - x1) + (wy - y1) * (y2 - y1)) / l2
            t = max(0, min(1, t))
            px = x1 + t * (x2 - x1)
            py = y1 + t * (y2 - y1)
            return math.sqrt((wx - px) ** 2 + (wy - py) ** 2) < 5 / self.app_state.zoom
        elif isinstance(shape, Text):
            return (
                shape.x <= wx <= shape.x + (len(shape.content) * shape.font_size * 0.6)
                and shape.y <= wy <= shape.y + shape.font_size
            )
        elif isinstance(shape, Path):
            if not shape.points:
                return False
            threshold = 10 / self.app_state.zoom
            for px, py in shape.points:
                if math.hypot(wx - px, wy - py) < threshold:
                    return True
            for i in range(len(shape.points) - 1):
                p1 = shape.points[i]
                p2 = shape.points[i + 1]
                x1, y1 = p1
                x2, y2 = p2
                l2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
                if l2 == 0:
                    continue
                t = ((wx - x1) * (x2 - x1) + (wy - y1) * (y2 - y1)) / l2
                t = max(0, min(1, t))
                px_proj = x1 + t * (x2 - x1)
                py_proj = y1 + t * (y2 - y1)
                if (
                    math.sqrt((wx - px_proj) ** 2 + (wy - py_proj) ** 2)
                    < 5 / self.app_state.zoom
                ):
                    return True
            return False
        elif isinstance(shape, Polygon):
            n = len(shape.points)
            inside = False
            p1x, p1y = shape.points[0]
            for i in range(n + 1):
                p2x, p2y = shape.points[i % n]
                if wy > min(p1y, p2y):
                    if wy <= max(p1y, p2y):
                        if wx <= max(p1x, p2x):
                            if p1y != p2y:
                                xinters = (wy - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                                if p1x == p2x or wx <= xinters:
                                    inside = not inside
                p1x, p1y = p2x, p2y
            return inside
        elif isinstance(shape, Group):
            for child in shape.children:
                if self._is_point_in_shape(child, wx, wy):
                    return True
        return False

    def hit_test(self, wx, wy, exclude_ids=None):
        if exclude_ids is None:
            exclude_ids = set()
        else:
            exclude_ids = set(exclude_ids)

        for shape in reversed(self.app_state.shapes):
            if shape.id in exclude_ids:
                continue

            if self._is_point_in_shape(shape, wx, wy):
                return shape

        return None

    def on_pan_start(self, e: ft.DragStartEvent):
        wx, wy = self.to_world(e.local_x, e.local_y)
        self.last_wx = wx
        self.last_wy = wy

        tool = self.tools.get(self.app_state.current_tool)
        if tool:
            tool.on_down(wx, wy, e)

    def on_pan_update(self, e: ft.DragUpdateEvent):
        wx, wy = self.to_world(e.local_x, e.local_y)
        self.last_wx = wx
        self.last_wy = wy

        tool = self.tools.get(self.app_state.current_tool)
        if tool:
            tool.on_move(wx, wy, e)

    def on_pan_end(self, e: ft.DragEndEvent):
        # DragEndEvent doesn't have coordinates, use last known
        wx, wy = self.last_wx, self.last_wy

        tool = self.tools.get(self.app_state.current_tool)
        if tool:
            tool.on_up(wx, wy, e)

        self.app_state.set_shift_key(False)

    def on_hover(self, e: ft.HoverEvent):
        self.hover_wx, self.hover_wy = self.to_world(e.local_x, e.local_y)

        # Some tools need hover updates (like LineTool for anchors)
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
