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
    radius: float = 0.0


@dataclass
class Text(Shape):
    type: str = "text"
    content: str = ""
    font_size: float = 16.0


@dataclass
class Path(Shape):
    type: str = "path"
    points: List[Tuple[float, float]] = field(default_factory=list)
