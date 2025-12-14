import flet as ft
from .base_drawer import BaseDrawer
from ...state.app_state import AppState


class FilesDrawer(BaseDrawer):
    def __init__(self, app_state: AppState, on_update_callback=None):
        super().__init__(app_state)
        self.on_update = on_update_callback
        self.expanded_paths = set()
        self.selected_folder_path = None
        self.creating_type = None  # 'file' or 'folder' or None

        self.creation_input = ft.TextField(
            height=30,
            text_size=12,
            content_padding=5,
            autofocus=True,
            on_submit=self._on_creation_submit,
        )

    def update(self):
        if self.on_update:
            self.on_update()

    def _toggle_path(self, path):
        if path in self.expanded_paths:
            self.expanded_paths.remove(path)
        else:
            self.expanded_paths.add(path)
        self.selected_folder_path = path  # Auto-select the clicked folder
        self.update()

    def _select_folder(self, path):
        self.selected_folder_path = path
        self.update()

    def _start_creation(self, type_):
        self.creating_type = type_
        self.creation_input.value = ""
        self.creation_input.error_text = None
        self.update()

    def _cancel_creation(self, e=None):
        self.creating_type = None
        self.update()

    def _on_creation_submit(self, e):
        name = self.creation_input.value
        if not name:
            self._cancel_creation()
            return

        # Prepend selected folder path if applicable
        if self.selected_folder_path:
            # Avoid double slash if path already ends with /
            prefix = self.selected_folder_path
            if prefix.endswith("/") and name.startswith("/"):
                full_name = prefix + name[1:]
            elif prefix.endswith("/") or name.startswith("/"):
                full_name = f"{prefix}{name}"
            else:
                full_name = f"{prefix}/{name}"
        else:
            full_name = name

        try:
            if self.creating_type == "folder":
                self.app_state.create_folder(full_name)
            else:
                self.app_state.create_file(full_name)
            self.creating_type = None
            self.update()
        except Exception as ex:
            self.creation_input.error_text = str(ex)
            self.creation_input.update()

    def _export_current_file(self):
        current_file = self.app_state.get_current_filename()
        if not current_file:
            return

        # Replace extension
        if current_file.endswith(".json"):
            export_name = current_file[:-5] + ".png"
        else:
            export_name = current_file + ".png"

        try:
            self.app_state.export_image(export_name)
            # Accessing page via app_state or a passed reference would be better,
            # but for now we might lose the snackbar functionality or need to pass a callback.
            # Assuming we can't easily show snackbar from here without passing page context.
            # We'll skip the snackbar for now or rely on AppState to handle notifications if we had that system.
            print(f"Exported to exports/{export_name}")
        except Exception as e:
            print(f"Export failed: {e}")

    def _on_file_click(self, path):
        # Get parent directory
        if "/" in path:
            parent_dir = path.rsplit("/", 1)[0] + "/"
            self.selected_folder_path = parent_dir
        else:
            self.selected_folder_path = None  # Root

        self.app_state.switch_file(path)

    def _get_files_content(self) -> list[ft.Control]:
        files = self.app_state.list_files()
        folders = self.app_state.list_folders()
        current_file = self.app_state.get_current_filename()

        # Build tree structure
        def build_tree(file_list, folder_list):
            tree = {"__files__": [], "__folders__": {}}

            def ensure_path(parts, current_node):
                for part in parts:
                    if not part:
                        continue
                    if part not in current_node["__folders__"]:
                        current_node["__folders__"][part] = {
                            "__files__": [],
                            "__folders__": {},
                        }
                    current_node = current_node["__folders__"][part]
                return current_node

            for folder in folder_list:
                parts = folder.replace("\\", "/").split("/")
                ensure_path(parts, tree)

            for f in file_list:
                parts = f.replace("\\", "/").split("/")
                ensure_path(parts[:-1], tree)["__files__"].append(parts[-1])
            return tree

        root_tree = build_tree(files, folders)

        # Recursive renderer
        def render_node(node, current_path, depth=0):
            controls = []
            indent = depth * 12  # Indentation per level

            # Render Folders
            for folder_name, folder_node in sorted(node["__folders__"].items()):
                full_path = f"{current_path}{folder_name}/"
                is_expanded = full_path in self.expanded_paths
                is_folder_selected = self.selected_folder_path == full_path

                # Folder Row
                controls.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                # Indent spacer
                                ft.Container(width=indent),
                                # Arrow
                                ft.Icon(
                                    ft.Icons.KEYBOARD_ARROW_DOWN
                                    if is_expanded
                                    else ft.Icons.KEYBOARD_ARROW_RIGHT,
                                    size=16,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                                # Icon
                                ft.Icon(
                                    ft.Icons.FOLDER_OPEN
                                    if is_expanded
                                    else ft.Icons.FOLDER,
                                    size=16,
                                    color=ft.Colors.BLUE_400,
                                ),
                                # Name
                                ft.Text(
                                    folder_name,
                                    size=13,
                                    weight=ft.FontWeight.W_500,
                                    expand=True,
                                ),
                                # Delete Action (Hover-like)
                                ft.IconButton(
                                    ft.Icons.DELETE_OUTLINE,
                                    icon_size=14,
                                    icon_color=ft.Colors.ON_SURFACE_VARIANT,
                                    tooltip="Delete Folder",
                                    on_click=lambda _,
                                    p=full_path.rstrip(
                                        "/"
                                    ): self.app_state.delete_folder(p),
                                ),
                            ],
                            spacing=5,
                        ),
                        padding=ft.padding.symmetric(vertical=2, horizontal=5),
                        ink=True,
                        on_click=lambda _, p=full_path: self._toggle_path(p),
                        border_radius=4,
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
                        if is_folder_selected
                        else None,
                        border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT)
                        if is_folder_selected
                        else None,
                    )
                )

                # Children (only if expanded)
                if is_expanded:
                    controls.extend(render_node(folder_node, full_path, depth + 1))

            # Render Files
            for filename in sorted(node["__files__"]):
                full_path = f"{current_path}{filename}"
                is_selected = full_path == current_file.replace("\\", "/")

                controls.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                # Indent spacer + Arrow spacer (16) + spacing (5)
                                ft.Container(width=indent + 21),
                                # Icon
                                ft.Icon(
                                    ft.Icons.INSERT_DRIVE_FILE_OUTLINED,
                                    size=16,
                                    color=ft.Colors.PRIMARY
                                    if is_selected
                                    else ft.Colors.ON_SURFACE_VARIANT,
                                ),
                                # Name
                                ft.Text(
                                    filename,
                                    size=13,
                                    color=ft.Colors.PRIMARY
                                    if is_selected
                                    else ft.Colors.ON_SURFACE,
                                    weight=ft.FontWeight.BOLD
                                    if is_selected
                                    else ft.FontWeight.NORMAL,
                                    expand=True,
                                ),
                                # Delete Action
                                ft.IconButton(
                                    ft.Icons.DELETE_OUTLINE,
                                    icon_size=14,
                                    icon_color=ft.Colors.ERROR
                                    if is_selected
                                    else ft.Colors.ON_SURFACE_VARIANT,
                                    tooltip="Delete File",
                                    on_click=lambda _,
                                    p=full_path: self.app_state.delete_file(p),
                                ),
                            ],
                            spacing=5,
                        ),
                        padding=ft.padding.symmetric(vertical=2, horizontal=5),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
                        if is_selected
                        else None,  # Subtle selection bg
                        border=ft.border.all(1, ft.Colors.PRIMARY)
                        if is_selected
                        else None,
                        border_radius=4,
                        ink=True,
                        on_click=lambda _, p=full_path: self._on_file_click(p),
                    )
                )

            return controls

        file_tree_controls = render_node(root_tree, "")

        # Creation Input Row (if active)
        if self.creating_type:
            creation_row = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.FOLDER
                            if self.creating_type == "folder"
                            else ft.Icons.INSERT_DRIVE_FILE,
                            size=16,
                            opacity=0.5,
                        ),
                        ft.Container(self.creation_input, expand=True),
                        ft.IconButton(
                            ft.Icons.CLOSE, icon_size=14, on_click=self._cancel_creation
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                padding=ft.padding.only(left=10, right=5, top=5),
            )
            file_tree_controls.insert(0, creation_row)

        return [
            # Header
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(
                            "EXPLORER",
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Container(expand=True),
                        ft.IconButton(
                            ft.Icons.CREATE_NEW_FOLDER_OUTLINED,
                            tooltip="New Folder",
                            icon_size=18,
                            on_click=lambda _: self._start_creation("folder"),
                        ),
                        ft.IconButton(
                            ft.Icons.NOTE_ADD_OUTLINED,
                            tooltip="New File",
                            icon_size=18,
                            on_click=lambda _: self._start_creation("file"),
                        ),
                        ft.Container(width=5),  # Spacer
                        ft.IconButton(
                            ft.Icons.IMAGE_OUTLINED,
                            tooltip="Export PNG",
                            icon_size=18,
                            on_click=lambda _: self._export_current_file(),
                        ),
                    ],
                ),
                padding=ft.padding.only(left=10, right=5, top=5, bottom=5),
            ),
            ft.Divider(height=1, thickness=1),
            # Tree List
            ft.Column(
                controls=file_tree_controls,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                spacing=0,  # Compact list
            ),
        ]

    def build(self) -> list[ft.Control]:
        return self._get_files_content()
