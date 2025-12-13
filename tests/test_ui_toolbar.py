import flet as ft
from blackboard.ui.toolbar import Toolbar
from blackboard.state.app_state import AppState
from blackboard.models import ToolType


def test_toolbar_initialization():
    app_state = AppState()
    toolbar = Toolbar(app_state)

    assert isinstance(toolbar, ft.Container)
    assert isinstance(toolbar.content, ft.Row)
    # Hand, Selection, Pen, Eraser, Line, Rect, Circle, Text = 8 buttons + divider + zoom out + zoom text + zoom in = 12 controls
    assert len(toolbar.content.controls) == 12


def test_toolbar_button_click():
    app_state = AppState()
    toolbar = Toolbar(app_state)

    # The controls are in order: HAND, SELECTION, PEN, ERASER, LINE, RECTANGLE, CIRCLE, TEXT
    row = toolbar.content
    assert isinstance(row, ft.Row), f"Toolbar content is not a Row, got {type(row)}"
    assert row.controls is not None, "Toolbar Row does not have 'controls' attribute"
    rect_btn = row.controls[5]  # Rectangle (was 4, now 5 because of Eraser)

    # Simulate click
    # For Flet Button, the event handler is usually 'on_click'
    # If 'on_click' is not available, try 'on_tap' or directly call the handler if accessible
    click_handler = getattr(rect_btn, "on_click", None)
    if callable(click_handler):
        click_handler(
            ft.ControlEvent(
                name="click", data=None, control=rect_btn, page=None, target="rect_btn"
            )
        )
    else:
        # Try 'on_tap' as an alternative
        tap_handler = getattr(rect_btn, "on_tap", None)
        if callable(tap_handler):
            tap_handler(
                ft.ControlEvent(
                    name="tap",
                    data=None,
                    control=rect_btn,
                    page=None,
                    target="rect_btn",
                )
            )
        else:
            raise AttributeError(
                "Rectangle button does not have an 'on_click' or 'on_tap' handler."
            )

    assert app_state.current_tool == ToolType.RECTANGLE


def test_toolbar_updates_ui_on_state_change():
    app_state = AppState()
    toolbar = Toolbar(app_state)

    # Manually call did_mount to attach listener since we aren't running in a full Flet app
    toolbar.did_mount()

    # Initial state HAND
    assert isinstance(toolbar.content, ft.Row), (
        f"Toolbar content is not a Row, got {type(toolbar.content)}"
    )
    assert toolbar.content.controls is not None, (
        "Toolbar Row does not have 'controls' attribute"
    )
    hand_btn = toolbar.content.controls[0]
    # Check if the button has 'icon_color' or 'color' attribute before asserting
    if hasattr(hand_btn, "icon_color"):
        assert getattr(hand_btn, "icon_color") == ft.Colors.BLUE  # Selected
    elif hasattr(hand_btn, "color"):
        assert getattr(hand_btn, "color") == ft.Colors.BLUE  # Selected
    else:
        raise AttributeError(
            f"Button does not have 'icon_color' or 'color' attribute, got attributes: {dir(hand_btn)}"
        )

    # Change state externally
    # We need to mock update() because toolbar.update() will be called by _on_state_change
    # and might fail if not attached to a page.
    toolbar.update = lambda: None

    app_state.set_tool(ToolType.PEN)

    # Now check UI
    hand_btn = toolbar.content.controls[0]
    pen_btn = toolbar.content.controls[2]

    is_dark = app_state.theme_mode == "dark"
    unselected_color = ft.Colors.WHITE if is_dark else ft.Colors.BLACK

    if hasattr(hand_btn, "icon_color"):
        assert getattr(hand_btn, "icon_color") == unselected_color
        assert getattr(pen_btn, "icon_color") == ft.Colors.BLUE
    elif hasattr(hand_btn, "color"):
        assert getattr(hand_btn, "color") == unselected_color
        assert getattr(pen_btn, "color") == ft.Colors.BLUE

    else:
        raise AttributeError(
            f"Button does not have 'icon_color' or 'color' attribute, got attributes: {dir(hand_btn)}"
        )
