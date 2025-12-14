import uuid
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


@dataclass
class Line(Shape):
    type: str = "line"
    end_x: float = 0.0
    end_y: float = 0.0


@dataclass
class Rectangle(Shape):
    type: str = "rectangle"
    width: float = 0.0
    height: float = 0.0


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
