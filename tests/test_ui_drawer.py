import flet as ft
from blackboard.ui.drawer import Drawer
from blackboard.state.app_state import AppState


def test_drawer_initialization():
    app_state = AppState()
    drawer = Drawer(app_state)

    # Should be hidden initially
    assert drawer.visible is False
    assert drawer.width == 300
    assert isinstance(drawer, ft.Container)


def test_drawer_opens_on_state_change():
    app_state = AppState()
    drawer = Drawer(app_state)
    drawer.did_mount()

    # Mock update
    drawer.update = lambda: None

    # Simulate rail click changing state
    app_state.set_active_drawer_tab("files")

    assert drawer.visible is True

    # Check content title
    # drawer.content is a Column
    column = drawer.content
    assert isinstance(column, ft.Column)

    # First item is close button row, second is title text
    title_text = column.controls[1]
    assert isinstance(title_text, ft.Text)
    assert title_text.value == "Files"


def test_drawer_content_changes():
    app_state = AppState()
    drawer = Drawer(app_state)
    drawer.did_mount()
    drawer.update = lambda: None

    # Tools tab
    app_state.set_active_drawer_tab("tools")
    title_text = drawer.content.controls[1]
    assert title_text.value == "Tool Settings"

    # Properties tab
    app_state.set_active_drawer_tab("properties")
    title_text = drawer.content.controls[1]
    assert title_text.value == "Properties"


def test_drawer_closes():
    app_state = AppState()
    drawer = Drawer(app_state)
    drawer.did_mount()
    drawer.update = lambda: None

    app_state.set_active_drawer_tab("files")
    assert drawer.visible is True

    app_state.close_drawer()
    assert drawer.visible is False


def test_drawer_files_tab_interaction():
    # Setup mock storage with predefined files
    from conftest import MockStorageService

    storage = MockStorageService()
    storage.files = ["file1.json", "file2.json"]
    storage.current_file = "file1.json"

    app_state = AppState(storage_service=storage)
    drawer = Drawer(app_state)
    drawer.did_mount()
    drawer.update = lambda: None

    # Open Files tab
    app_state.set_active_drawer_tab("files")

    # Check structure:
    # [0] Row(CloseButton)
    # [1] Text("Files")
    # [2] Divider
    # [3] Row(TextField, IconButton(Add))
    # [4] Divider
    # [5] Column(FileList)

    column = drawer.content
    assert len(column.controls) >= 6

    # Check New File Input
    new_file_row = column.controls[3]
    assert isinstance(new_file_row, ft.Row)
    input_field = new_file_row.controls[0]
    add_button = new_file_row.controls[1]
    assert isinstance(input_field, ft.TextField)
    assert isinstance(add_button, ft.IconButton)

    # Test Create File
    input_field.value = "new_project"
    # Manually trigger on_click handler
    drawer._on_create_file_click(None)

    assert "new_project.json" in app_state.list_files()
    assert app_state.get_current_filename() == "new_project.json"
    assert input_field.value == ""  # Should clear input

    # Re-fetch content as it was replaced during render
    column = drawer.content

    # Check File List
    file_list_col = column.controls[5]
    assert isinstance(file_list_col, ft.Column)
    # Should have 3 files now (file1, file2, new_project)
    assert len(file_list_col.controls) == 3

    # Test Switch File (click on first item - file1.json)
    file1_item = file_list_col.controls[0]  # file1.json
    file1_item.on_click(None)
    assert app_state.get_current_filename() == "file1.json"

    # Test Delete File (click delete on new_project.json - last item)
    new_project_item = file_list_col.controls[2]  # new_project.json
    # Structure of item content: Row([Icon, Text, DeleteButton])
    delete_btn = new_project_item.content.controls[2]
    delete_btn.on_click(None)

    assert "new_project.json" not in app_state.list_files()
