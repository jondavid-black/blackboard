from whiteboard.models import Shape, Line, Rectangle, Circle, Text, Path, ToolType


def test_shape_defaults():
    shape = Shape()
    assert shape.id is not None
    assert shape.type == "shape"
    assert shape.x == 0.0
    assert shape.y == 0.0
    assert shape.stroke_color == "black"
    assert shape.stroke_width == 2.0
    assert shape.filled is False
    assert shape.fill_color == "transparent"


def test_line_defaults():
    line = Line()
    assert line.type == "line"
    assert line.end_x == 0.0
    assert line.end_y == 0.0


def test_rectangle_defaults():
    rect = Rectangle()
    assert rect.type == "rectangle"
    assert rect.width == 0.0
    assert rect.height == 0.0


def test_circle_defaults():
    circle = Circle()
    assert circle.type == "circle"
    assert circle.radius == 0.0


def test_text_defaults():
    text = Text()
    assert text.type == "text"
    assert text.content == ""
    assert text.font_size == 16.0


def test_path_defaults():
    path = Path()
    assert path.type == "path"
    assert path.points == []


def test_tool_types():
    assert ToolType.HAND.value == "hand"
    assert ToolType.SELECTION.value == "selection"
    assert ToolType.LINE.value == "line"
    assert ToolType.RECTANGLE.value == "rectangle"
    assert ToolType.CIRCLE.value == "circle"
    assert ToolType.TEXT.value == "text"
    assert ToolType.PEN.value == "pen"
