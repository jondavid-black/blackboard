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

    # Structure:
    # [0] Close Button Row
    # [1] Header (Row[Text(EXPLORER), Spacer, IconButton(New Folder), IconButton(New File)])
    # [2] Divider
    # [3] Column(FileList)

    header_container = column.controls[1]
    assert isinstance(header_container, ft.Container)
    header_row = header_container.content
    assert isinstance(header_row, ft.Row)

    title_text = header_row.controls[0]
    assert isinstance(title_text, ft.Text)
    assert title_text.value == "EXPLORER"

    # [0] Header
    # [1] Divider
    # [2] Column(Tree)
    assert len(column.controls) >= 3


def test_drawer_content_changes():
    app_state = AppState()
    drawer = Drawer(app_state)
    drawer.did_mount()
    drawer.update = lambda: None

    # Tools tab
    app_state.set_active_drawer_tab("tools")
    # For non-files tabs:
    # [0] Close Button Row
    # [1] Title Text
    # ...
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
    # [0] Close Button
    # [1] Header (Row[Text(EXPLORER), Spacer, IconButton(New Folder), IconButton(New File)])
    # [2] Divider
    # [3] Column(FileList)

    column = drawer.content
    assert len(column.controls) >= 4

    # Get New File Button from Header
    # header_row = column.controls[1].content
    # Controls: [Text, Spacer, NewFolderBtn, NewFileBtn]
    # new_file_btn = header_row.controls[3]

    # Simulate clicking New File
    # This sets creating_type = 'file' and calls update()
    # We need to manually trigger the lambda
    files_drawer = drawer.drawers["files"]
    files_drawer._start_creation("file")

    # Re-fetch content because it re-renders
    # drawer.content is the Column
    # It delegates to files_drawer.build(), which returns controls
    # The Column controls are: [CloseButton, Header, Divider, TreeColumn]
    column = drawer.content
    file_list_col = column.controls[3]

    # Now the first item in file_list_col should be the creation row
    # because FilesDrawer.build() logic puts creation row at top if active
    creation_row_container = file_list_col.controls[0]
    creation_row = creation_row_container.content
    assert isinstance(creation_row, ft.Row)

    # In previous error: 'Icon' object has no attribute 'content'
    # Let's check structure of creation row in FilesDrawer._get_files_content
    # Row controls: [Icon(FOLDER/FILE), Container(TextField), IconButton(CLOSE)]
    # So index 1 is the Container holding the TextField
    input_container = creation_row.controls[1]
    assert isinstance(input_container, ft.Container)
    input_field = input_container.content  # This should be the TextField
    assert isinstance(input_field, ft.TextField)

    # Test Create File
    input_field.value = "new_project"
    # Manually trigger on_submit handler
    files_drawer._on_creation_submit(None)

    assert "new_project.json" in app_state.list_files()
    assert app_state.get_current_filename() == "new_project.json"

    # Re-fetch content
    # Note: drawer._render_content() is called on update usually,
    # but here we might need to manually invoke if we are not running full Flet loop
    # or ensure our test drawer is updating.
    # The files_drawer update calls self.on_update which calls drawer.update...
    # But since we mocked drawer.update = lambda: None, we need to manually rebuild content
    # or inspect what files_drawer WOULD return.

    # Let's inspect files_drawer state/logic directly or manually rebuild drawer content
    drawer._render_content()
    column = drawer.content
    file_list_col = column.controls[3]

    # Creation row should be gone, only files/folders
    # Files: file1.json, file2.json, new_project.json -> 3 items
    assert len(file_list_col.controls) == 3

    # Test Switch File (click on first item - file1.json)
    # Item structure: Container(Row([Spacer, Arrow, Icon, Text, DeleteBtn]))
    file1_item = file_list_col.controls[0]
    file1_item.on_click(None)
    assert app_state.get_current_filename() == "file1.json"

    # Test Delete File (click delete on new_project.json - last item)
    new_project_item = file_list_col.controls[2]
    row = new_project_item.content
    # Controls: [Spacer, Icon, Name, DeleteBtn] -> Wait, index might vary due to arrow?
    # Let's check the render function:
    # controls=[Container(width), Icon(file), Text(name), IconButton(delete)]
    delete_btn = row.controls[3]
    delete_btn.on_click(None)

    assert "new_project.json" not in app_state.list_files()


def test_drawer_shows_empty_folders():
    # Setup mock storage with an empty folder
    from conftest import MockStorageService

    storage = MockStorageService()
    storage.files = []
    storage.create_folder("empty_folder")

    app_state = AppState(storage_service=storage)
    drawer = Drawer(app_state)
    drawer.did_mount()
    drawer.update = lambda: None

    app_state.set_active_drawer_tab("files")

    # Navigate to the file list column
    column = drawer.content
    file_list_col = column.controls[3]

    # Should see the empty folder
    assert len(file_list_col.controls) == 1
    folder_container = file_list_col.controls[0]
    folder_row = folder_container.content

    # Folder Row: [Spacer, Arrow, Icon, Text, Delete]
    folder_name_text = folder_row.controls[3]
    assert folder_name_text.value == "empty_folder"


def test_drawer_folder_interaction():
    # Setup mock storage
    from conftest import MockStorageService

    storage = MockStorageService()
    storage.files = []
    # Create a file inside a folder
    storage.create_folder("my_folder")
    storage.create_file("my_folder/nested_file.json")

    app_state = AppState(storage_service=storage)
    drawer = Drawer(app_state)
    drawer.did_mount()
    drawer.update = lambda: None

    app_state.set_active_drawer_tab("files")

    # 1. Verify Folder is initially collapsed (files inside shouldn't be visible)
    # Structure: Header, Divider, TreeColumn
    tree_col = drawer.content.controls[3]

    # Expecting: 1 item (the folder "my_folder")
    assert len(tree_col.controls) == 1

    folder_container = tree_col.controls[0]
    folder_row = folder_container.content
    # Row controls: [Indent, Arrow, Icon, Text, Delete]
    arrow_icon = folder_row.controls[1]

    # Should be arrow RIGHT (collapsed)
    assert arrow_icon.name == ft.Icons.KEYBOARD_ARROW_RIGHT

    # 2. Click to Expand
    # The container has the on_click handler
    folder_container.on_click(None)

    # Re-fetch tree column
    tree_col = drawer.content.controls[3]

    # Expecting: 2 items (Folder "my_folder" + File "nested_file.json")
    assert len(tree_col.controls) == 2

    # Check Folder Icon is now DOWN
    folder_container_expanded = tree_col.controls[0]
    arrow_icon_expanded = folder_container_expanded.content.controls[1]
    assert arrow_icon_expanded.name == ft.Icons.KEYBOARD_ARROW_DOWN

    # Check Nested File
    file_container = tree_col.controls[1]
    file_row = file_container.content
    # Row controls: [Indent(width), Icon, Name, Delete]
    # Note: File rows don't have a separate Arrow icon, just indentation

    file_name = file_row.controls[2]
    assert file_name.value == "nested_file.json"

    # Check Indentation
    # Folder indent is 0
    folder_indent = folder_container_expanded.content.controls[0].width
    assert folder_indent == 0

    # File indent should be > 0 (12 * 1 level + 21 for arrow spacer) = 33
    file_indent_spacer = file_row.controls[0]
    assert file_indent_spacer.width > 0


def test_drawer_creation_in_selected_folder():
    # Setup mock storage
    from conftest import MockStorageService

    storage = MockStorageService()
    storage.files = []
    storage.create_folder("parent_folder")

    app_state = AppState(storage_service=storage)
    drawer = Drawer(app_state)
    drawer.did_mount()
    drawer.update = lambda: None

    app_state.set_active_drawer_tab("files")

    # 1. Select the folder
    # tree_col = drawer.content.controls[3]
    # folder_container = tree_col.controls[0]

    # Simulate clicking the folder (which toggles it AND selects it now)
    # The on_click lambda calls _toggle_path
    # We need to manually simulate this behavior since we can't click the lambda directly easily
    # or rely on the bound method.
    # The simpler way is calling _toggle_path directly with the folder name
    files_drawer = drawer.drawers["files"]
    files_drawer._toggle_path("parent_folder/")

    assert files_drawer.selected_folder_path == "parent_folder/"

    # 2. Start creation of a file
    files_drawer._start_creation("file")

    # 3. Submit name "child_file"
    files_drawer.creation_input.value = "child_file"
    files_drawer._on_creation_submit(None)

    # 4. Verify file was created INSIDE the folder
    assert "parent_folder/child_file.json" in app_state.list_files()

    # Verify we are switched to it
    assert app_state.get_current_filename() == "parent_folder/child_file.json"

    # 5. Verify creation creates in root if NO folder selected
    # Deselect folder (click file in root or just reset)
    files_drawer.selected_folder_path = None

    files_drawer._start_creation("file")
    files_drawer.creation_input.value = "root_file"
    files_drawer._on_creation_submit(None)

    assert "root_file.json" in app_state.list_files()
