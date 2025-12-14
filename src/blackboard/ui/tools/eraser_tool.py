import math
from .base_tool import BaseTool
from ...models import Path


class EraserTool(BaseTool):
    def on_down(self, x: float, y: float, e):
        hit_shape = self.canvas.hit_test(x, y)
        if hit_shape:
            if isinstance(hit_shape, Path):
                # For Path, eraser drag interaction will be handled in on_move (pan_update).
                # But if we just click, we might want to delete the whole path?
                # The legacy code was a bit ambiguous but handled it like this:
                # If it's a path, start erasing points immediately.
                self._erase_points_in_path(hit_shape, x, y)
            else:
                # For other shapes, delete immediately
                self.app_state.remove_shape(hit_shape)

    def on_move(self, x: float, y: float, e):
        # Continuous hit testing while dragging
        hit_shape = self.canvas.hit_test(x, y)
        if hit_shape and isinstance(hit_shape, Path):
            self._erase_points_in_path(hit_shape, x, y)

    def on_up(self, x: float, y: float, e):
        pass

    def _erase_points_in_path(self, path: Path, wx: float, wy: float):
        # Eraser radius in world coordinates
        eraser_radius = 10 / self.app_state.zoom

        # Find points to remove
        # We need to preserve the order and split if necessary.
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
            if len(path.points) < 1:
                self.app_state.remove_shape(path)
            else:
                self.app_state.update_shape(path)
        else:
            # We have multiple segments.
            # Update the original path to be the first segment
            first_seg = new_points_list[0]
            path.points = first_seg
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
