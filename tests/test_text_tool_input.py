import flet as ft
from unittest.mock import MagicMock
from blackboard.ui.canvas import BlackboardCanvas
from blackboard.state.app_state import AppState
from blackboard.models import ToolType
from conftest import MockStorageService


def test_text_tool_creates_input_field():
    storage = MockStorageService()
    app_state = AppState(storage_service=storage)
    app_state.set_tool(ToolType.TEXT)

    # We need to initialize the canvas to have the new structure
    # But since we haven't modified the code yet, this test is expected to fail
    # or error out if we try to access non-existent attributes.
    # So this serves as TDD.

    canvas = BlackboardCanvas(app_state)

    # Mock update
    canvas.update = lambda: None

    # We removed ui_stack in favor of Dialog, so we don't mock it anymore

    # Mock event

    e = MagicMock(spec=ft.DragStartEvent)
    e.local_x = 100
    e.local_y = 100
    e.global_x = 100
    e.global_y = 100

    # Action
    canvas.on_pan_start(e)

    # Assertions for NEW behavior (Dialog)
    # We can't easily check for open dialogs on the page mock without a real page integration test.
    # But we can check if self.page.open was called if we mock self.page

    # We need to inject a mock page into the canvas
    mock_page = MagicMock(spec=ft.Page)
    canvas.page = mock_page

    # Action again with page
    canvas.on_pan_start(e)

    # Check if dialog was opened
    assert mock_page.open.called
    args = mock_page.open.call_args[0]
    dlg = args[0]
    assert isinstance(dlg, ft.AlertDialog)
    assert dlg.title.value == "Add Text"
    assert isinstance(dlg.content, ft.TextField)
