from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont
import os
from ..models import Shape, Line, Rectangle, Circle, Text, Path, Polygon


class Exporter:
    def export_to_png(self, shapes: List[Shape], output_path: str, padding: int = 50):
        if not shapes:
            # Create a blank image if no shapes
            img = Image.new("RGB", (800, 600), "white")
            img.save(output_path)
            return

        # 1. Calculate Bounding Box
        min_x, min_y = float("inf"), float("inf")
        max_x, max_y = float("-inf"), float("-inf")

        for shape in shapes:
            bounds = self._get_bounds(shape)
            if bounds:
                min_x = min(min_x, bounds[0])
                min_y = min(min_y, bounds[1])
                max_x = max(max_x, bounds[2])
                max_y = max(max_y, bounds[3])

        if min_x == float("inf"):
            min_x, min_y, max_x, max_y = 0, 0, 800, 600

        # Add padding
        width = int(max_x - min_x + (padding * 2))
        height = int(max_y - min_y + (padding * 2))

        # Ensure positive dimensions
        width = max(100, width)
        height = max(100, height)

        # 2. Create Image
        # Use RGBA for transparency support if needed, but RGB with white bg is standard
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)

        # 3. Draw Shapes
        # We need to offset all shapes by (-min_x + padding, -min_y + padding)
        offset_x = -min_x + padding
        offset_y = -min_y + padding

        for shape in shapes:
            self._draw_shape(draw, shape, offset_x, offset_y)

        # 4. Save
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
        print(f"Exported image to {output_path}")

    def _get_bounds(self, shape: Shape) -> Tuple[float, float, float, float] | None:
        """Returns (min_x, min_y, max_x, max_y)"""
        if isinstance(shape, Line):
            return (
                min(shape.x, shape.end_x),
                min(shape.y, shape.end_y),
                max(shape.x, shape.end_x),
                max(shape.y, shape.end_y),
            )
        elif isinstance(shape, Rectangle):
            return (
                shape.x,
                shape.y,
                shape.x + shape.width,
                shape.y + shape.height,
            )
        elif isinstance(shape, Circle):
            return (
                shape.x,
                shape.y,
                shape.x + (shape.radius_x * 2),
                shape.y + (shape.radius_y * 2),
            )
        elif isinstance(shape, Text):
            # Estimate text size (rough approximation without font metrics)
            # Assuming ~0.6 * font_size width per char
            w = len(shape.content) * shape.font_size * 0.6
            h = shape.font_size
            return (shape.x, shape.y, shape.x + w, shape.y + h)
        elif isinstance(shape, Path) or isinstance(shape, Polygon):
            if not shape.points:
                return None
            xs = [p[0] for p in shape.points]
            ys = [p[1] for p in shape.points]
            return (min(xs), min(ys), max(xs), max(ys))
        return None

    def _draw_shape(
        self, draw: ImageDraw.ImageDraw, shape: Shape, off_x: float, off_y: float
    ):
        # Resolve colors
        stroke_color = shape.stroke_color if shape.stroke_color else "black"
        # PIL doesn't support "transparent" string or hex with alpha easily in RGB mode
        # Simple mapping for common names
        if stroke_color == "transparent":
            stroke_color = None

        fill_color = shape.fill_color if shape.filled else None
        if fill_color == "transparent":
            fill_color = None

        width = int(shape.stroke_width)

        if isinstance(shape, Line):
            draw.line(
                [
                    (shape.x + off_x, shape.y + off_y),
                    (shape.end_x + off_x, shape.end_y + off_y),
                ],
                fill=stroke_color,
                width=width,
            )
            # Arrow handling (simplified)
            if hasattr(shape, "line_type") and shape.line_type == "arrow":
                # Calculate angle and draw small lines
                import math

                dx = shape.end_x - shape.x
                dy = shape.end_y - shape.y
                angle = math.atan2(dy, dx)
                arrow_len = 15
                arrow_angle = math.pi / 6

                ex, ey = shape.end_x + off_x, shape.end_y + off_y

                ax1 = ex - arrow_len * math.cos(angle - arrow_angle)
                ay1 = ey - arrow_len * math.sin(angle - arrow_angle)
                ax2 = ex - arrow_len * math.cos(angle + arrow_angle)
                ay2 = ey - arrow_len * math.sin(angle + arrow_angle)

                draw.line([(ex, ey), (ax1, ay1)], fill=stroke_color, width=width)
                draw.line([(ex, ey), (ax2, ay2)], fill=stroke_color, width=width)

        elif isinstance(shape, Rectangle):
            draw.rectangle(
                [
                    (shape.x + off_x, shape.y + off_y),
                    (shape.x + shape.width + off_x, shape.y + shape.height + off_y),
                ],
                outline=stroke_color,
                fill=fill_color,
                width=width,
            )

        elif isinstance(shape, Circle):
            draw.ellipse(
                [
                    (shape.x + off_x, shape.y + off_y),
                    (
                        shape.x + (shape.radius_x * 2) + off_x,
                        shape.y + (shape.radius_y * 2) + off_y,
                    ),
                ],
                outline=stroke_color,
                fill=fill_color,
                width=width,
            )

        elif isinstance(shape, Text):
            # Try to load a font, otherwise default
            try:
                # This is platform dependent. For now use default load_default()
                # or a simple path if we had one.
                font = ImageFont.load_default()
                # Default font doesn't scale well.
                # In a real app we'd bundle a TTF.
            except Exception:
                font = None

            draw.text(
                (shape.x + off_x, shape.y + off_y),
                shape.content,
                fill=stroke_color,
                font=font,
            )

        elif isinstance(shape, Path) or isinstance(shape, Polygon):
            if not shape.points:
                return
            points = [(p[0] + off_x, p[1] + off_y) for p in shape.points]

            if isinstance(shape, Polygon):
                # Polygon is closed
                draw.polygon(
                    points, outline=stroke_color, fill=fill_color
                )  # width not supported in polygon for outline?
                # Draw outline manually if width > 1
                if width >= 1 and stroke_color:
                    points.append(points[0])
                    draw.line(points, fill=stroke_color, width=width)
            else:
                # Path is open
                draw.line(points, fill=stroke_color, width=width)
