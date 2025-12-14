import flet as ft
from ..state.app_state import AppState


class Drawer(ft.Container):
    def __init__(self, app_state: AppState):
        self.app_state = app_state
        self.expanded_paths = set()
        self.selected_folder_path = None  # To track selected folder for creation
        self.creating_type = None  # 'file' or 'folder' or None

        # Input for creating new items
        self.creation_input = ft.TextField(
            height=30,
            text_size=12,
            content_padding=5,
            autofocus=True,
            on_submit=self._on_creation_submit,
        )

        super().__init__(
            width=300,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=0,  # Remove padding to go edge-to-edge
            visible=False,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.BLACK54,
            ),
        )
        self._render_content()

    def did_mount(self):
        self.app_state.add_listener(self._on_state_change)
        self._update_visibility()

    def will_unmount(self):
        self.app_state.remove_listener(self._on_state_change)

    def _on_state_change(self):
        self._update_visibility()
        self._render_content()
        self.update()

    def _update_visibility(self):
        self.visible = self.app_state.active_drawer_tab is not None

    def _toggle_path(self, path):
        if path in self.expanded_paths:
            self.expanded_paths.remove(path)
        else:
            self.expanded_paths.add(path)
        self.selected_folder_path = path  # Auto-select the clicked folder
        self._render_content()
        self.update()

    def _select_folder(self, path):
        self.selected_folder_path = path
        self._render_content()
        self.update()

    def _start_creation(self, type_):
        self.creating_type = type_
        self.creation_input.value = ""
        self.creation_input.error_text = None
        self._render_content()
        self.update()

    def _cancel_creation(self, e=None):
        self.creating_type = None
        self._render_content()
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
            self._render_content()
            self.update()
        except Exception as ex:
            self.creation_input.error_text = str(ex)
            self.creation_input.update()

    def _get_files_content(self):
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
                # Selection logic for folders (distinct from current file)
                # We strip trailing slash for cleaner comparison if needed, but path usually has it
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

    def _on_file_click(self, path):
        # Deselect any folder when a file is clicked,
        # or maybe we want to keep the folder selected?
        # Usually file click means "open file".
        # Let's clear folder selection to avoid confusion about where the NEXT create goes.
        # Or, we could set selected_folder_path to the file's parent?
        # VS Code style: clicking a file sets focus there, creating new items usually goes to parent dir.

        # Get parent directory
        if "/" in path:
            parent_dir = path.rsplit("/", 1)[0] + "/"
            self.selected_folder_path = parent_dir
        else:
            self.selected_folder_path = None  # Root

        self.app_state.switch_file(path)
        # switch_file triggers notify -> render, but we updated local state too

    def _get_layers_content(self):
        shapes = list(
            reversed(self.app_state.shapes)
        )  # Reverse to show top layers first
        if not shapes:
            return [
                ft.Container(
                    content=ft.Text("No items on canvas", color=ft.Colors.GREY),
                    padding=10,
                )
            ]

        layer_controls = []
        for shape in shapes:
            is_selected = shape.id in self.app_state.selected_shape_ids
            # Determine icon based on shape type
            icon = ft.Icons.CHECK_BOX_OUTLINE_BLANK
            if shape.type == "line":
                icon = ft.Icons.SHOW_CHART
            elif shape.type == "text":
                icon = ft.Icons.TEXT_FIELDS
            elif shape.type == "circle":
                icon = ft.Icons.CIRCLE_OUTLINED
            elif shape.type == "rectangle":
                icon = ft.Icons.RECTANGLE_OUTLINED
            elif shape.type == "polygon":
                icon = ft.Icons.POLYLINE
            elif shape.type == "path":
                icon = ft.Icons.GESTURE

            layer_controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(
                                icon,
                                size=16,
                                color=ft.Colors.PRIMARY if is_selected else None,
                            ),
                            ft.Text(
                                f"{shape.type.capitalize()} ({shape.id[:4]})",
                                size=13,
                                weight=ft.FontWeight.BOLD
                                if is_selected
                                else ft.FontWeight.NORMAL,
                                expand=True,
                            ),
                            ft.IconButton(
                                ft.Icons.ARROW_UPWARD,
                                icon_size=14,
                                tooltip="Move Forward",
                                on_click=lambda _,
                                s=shape.id: self.app_state.move_shape_forward(s),
                            ),
                            ft.IconButton(
                                ft.Icons.ARROW_DOWNWARD,
                                icon_size=14,
                                tooltip="Move Backward",
                                on_click=lambda _,
                                s=shape.id: self.app_state.move_shape_backward(s),
                            ),
                        ],
                        spacing=5,
                    ),
                    padding=ft.padding.symmetric(vertical=5, horizontal=10),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
                    if is_selected
                    else None,
                    border_radius=4,
                    ink=True,
                    on_click=lambda _, s=shape.id: self.app_state.select_shape(s),
                )
            )

        return [
            ft.Text("Layers", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Column(controls=layer_controls, scroll=ft.ScrollMode.AUTO, expand=True),
        ]

    def _get_properties_content(self):
        selected_ids = self.app_state.selected_shape_ids
        if not selected_ids:
            return [
                ft.Text("Properties", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("No selection", italic=True),
            ]

        # Get first selected shape as representative for initial values
        first_shape = None
        for s in self.app_state.shapes:
            if s.id in list(selected_ids)[0]:
                first_shape = s
                break

        if not first_shape:
            return [
                ft.Text("Properties", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("Selection error", italic=True),
            ]

        def on_stroke_width_change(e):
            self.app_state.update_selected_shapes_properties(
                stroke_width=float(e.control.value)
            )

        def on_opacity_change(e):
            self.app_state.update_selected_shapes_properties(
                opacity=float(e.control.value) / 100
            )

        def on_stroke_color_change(e):
            self.app_state.update_selected_shapes_properties(
                stroke_color=e.control.content.bgcolor
            )

        def on_fill_color_change(e):
            color = e.control.content.bgcolor
            filled = color != "transparent"
            self.app_state.update_selected_shapes_properties(
                fill_color=color, filled=filled
            )

        def on_line_style_change(e):
            style = e.control.value
            dash_array = None
            if style == "Dashed":
                dash_array = [10, 10]
            elif style == "Dotted":
                dash_array = [5, 5]
            self.app_state.update_selected_shapes_properties(
                stroke_dash_array=dash_array
            )

        # Helper to create color swatch
        def create_color_swatch(color, current_color, on_click):
            is_selected = current_color == color
            return ft.Container(
                width=24,
                height=24,
                bgcolor=color if color != "transparent" else None,
                border=ft.border.all(
                    2, ft.Colors.BLUE if is_selected else ft.Colors.OUTLINE
                )
                if color == "transparent"
                else None,
                border_radius=12,
                content=ft.Container(bgcolor=color)
                if color != "transparent"
                else ft.Icon(ft.Icons.BLOCK, size=16),
                on_click=on_click,
                ink=True,
            )

        colors = [
            ft.Colors.BLACK,
            ft.Colors.WHITE,
            ft.Colors.RED,
            ft.Colors.GREEN,
            ft.Colors.BLUE,
            ft.Colors.YELLOW,
            ft.Colors.PURPLE,
            "transparent",
        ]

        # Stroke Color Swatches
        stroke_swatches = ft.Row(wrap=True, spacing=5)
        for c in colors[:-1]:  # No transparent stroke usually
            stroke_swatches.controls.append(
                create_color_swatch(c, first_shape.stroke_color, on_stroke_color_change)
            )

        # Fill Color Swatches
        fill_swatches = ft.Row(wrap=True, spacing=5)
        for c in colors:
            fill_swatches.controls.append(
                create_color_swatch(c, first_shape.fill_color, on_fill_color_change)
            )

        current_style = "Solid"
        if first_shape.stroke_dash_array == [10, 10]:
            current_style = "Dashed"
        elif first_shape.stroke_dash_array == [5, 5]:
            current_style = "Dotted"

        return [
            ft.Text("Properties", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text(f"Selection: {len(selected_ids)} items"),
            ft.Container(height=10),
            ft.Text("Stroke Width"),
            ft.Slider(
                min=1,
                max=20,
                divisions=19,
                value=first_shape.stroke_width,
                label="{value}",
                on_change=on_stroke_width_change,
            ),
            ft.Text("Opacity"),
            ft.Slider(
                min=0,
                max=100,
                divisions=100,
                value=first_shape.opacity * 100,
                label="{value}%",
                on_change=on_opacity_change,
            ),
            ft.Text("Line Style"),
            ft.Dropdown(
                value=current_style,
                options=[
                    ft.dropdown.Option("Solid"),
                    ft.dropdown.Option("Dashed"),
                    ft.dropdown.Option("Dotted"),
                ],
                on_change=on_line_style_change,
            ),
            ft.Text("Stroke Color"),
            stroke_swatches,
            ft.Container(height=10),
            ft.Text("Fill Color"),
            fill_swatches,
        ]

    def _render_content(self):
        tab = self.app_state.active_drawer_tab

        content_map = {
            "tools": [
                ft.Text("Tool Settings", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("Stroke Width"),
                ft.Slider(min=1, max=10, divisions=9, label="{value}"),
                ft.Text("Opacity"),
                ft.Slider(min=0, max=100, divisions=100, label="{value}%"),
            ],
            "profile": [
                ft.Text("User Profile", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.PERSON, size=40),
                    radius=40,
                ),
                ft.Container(height=10),
                ft.Text("User Name", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("user@example.com", color=ft.Colors.GREY),
                ft.Container(height=20),
                ft.OutlinedButton("Sign Out", icon=ft.Icons.LOGOUT),
            ],
        }

        if tab == "files":
            current_content = self._get_files_content()
            # Special case for files: remove padding from parent container to allow full bleed
            self.padding = 0
        elif tab == "layers":
            current_content = self._get_layers_content()
            self.padding = 10
        elif tab == "properties":
            current_content = self._get_properties_content()
            self.padding = 10
        else:
            current_content = content_map.get(tab, [])
            # Restore padding for other tabs
            self.padding = 10

        self.content = ft.Column(
            controls=[
                # Close button row
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                on_click=lambda _: self.app_state.close_drawer(),
                            )
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    padding=5,
                ),
                *current_content,
            ],
            spacing=0 if tab == "files" else 10,
        )
