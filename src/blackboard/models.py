import uuid
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple


class ToolType(Enum):
    HAND = "hand"
    SELECTION = "selection"
    LINE = "line"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    TEXT = "text"
    PEN = "pen"
    ERASER = "eraser"
    POLYGON = "polygon"


@dataclass
class Shape:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "shape"
    x: float = 0.0
    y: float = 0.0
    stroke_color: str = ""  # Empty means use theme default
    stroke_width: float = 2.0
    filled: bool = False
    fill_color: str = "transparent"

    def get_anchors(self) -> List[Tuple[str, float, float]]:
        """Returns a list of (anchor_id, x, y) tuples."""
        return []


@dataclass
class Line(Shape):
    type: str = "line"
    end_x: float = 0.0
    end_y: float = 0.0
    line_type: str = "simple"  # simple, arrow, connector, angle_connector
    start_shape_id: str | None = None
    end_shape_id: str | None = None
    start_anchor_id: str | None = (
        None  # e.g. "top", "bottom", "left", "right", "tl", "tr", "bl", "br"
    )
    end_anchor_id: str | None = None


@dataclass
class Rectangle(Shape):
    type: str = "rectangle"
    width: float = 0.0
    height: float = 0.0

    def get_anchors(self) -> List[Tuple[str, float, float]]:
        x, y, w, h = self.x, self.y, self.width, self.height
        return [
            ("top_left", x, y),
            ("top_right", x + w, y),
            ("bottom_right", x + w, y + h),
            ("bottom_left", x, y + h),
            ("top_center", x + w / 2, y),
            ("right_center", x + w, y + h / 2),
            ("bottom_center", x + w / 2, y + h),
            ("left_center", x, y + h / 2),
        ]


@dataclass
class Circle(Shape):
    type: str = "circle"
    radius_x: float = 0.0
    radius_y: float = 0.0

    @property
    def radius(self) -> float:
        """Compat for code expecting a single radius (returns average or max?)
        Let's return max for bounding box logic usually.
        Actually, old code expects .radius to exist.
        """
        return max(abs(self.radius_x), abs(self.radius_y))

    @radius.setter
    def radius(self, value: float):
        self.radius_x = value
        self.radius_y = value

    def get_anchors(self) -> List[Tuple[str, float, float]]:
        cx = self.x + self.radius_x
        cy = self.y + self.radius_y
        rx, ry = self.radius_x, self.radius_y
        return [
            ("top_center", cx, cy - ry),
            ("right_center", cx + rx, cy),
            ("bottom_center", cx, cy + ry),
            ("left_center", cx - rx, cy),
        ]


@dataclass
class Text(Shape):
    type: str = "text"
    content: str = ""
    font_size: float = 16.0


@dataclass
class Path(Shape):
    type: str = "path"
    points: List[Tuple[float, float]] = field(default_factory=list)


@dataclass
class Polygon(Shape):
    type: str = "polygon"
    points: List[Tuple[float, float]] = field(default_factory=list)
    polygon_type: str = (
        "triangle"  # triangle, diamond, pentagon, hexagon, octagon, star
    )

    def get_anchors(self) -> List[Tuple[str, float, float]]:
        anchors = []
        for i, p in enumerate(self.points):
            anchors.append((f"vertex_{i}", p[0], p[1]))
        return anchors
