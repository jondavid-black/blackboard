from typing import List, Callable, Optional, TYPE_CHECKING
from ..models import Shape, ToolType, Line, Polygon, Group
from ..storage.storage_service import StorageService
from ..storage.exporter import Exporter

if TYPE_CHECKING:
    pass


class AppState:
    def __init__(self, storage_service: Optional[StorageService] = None):
        self.storage = storage_service or StorageService()
        self.shapes = []  # Initialize empty first
        self.selected_shape_ids: set[str] = set()

        # Then load data if we can, but tests might rely on empty start
        # Actually the problem is that load_data() loads from default.json which might have existing data
        # We should accept an optional argument to skip loading or load from memory?
        # Better: tests should mock StorageService or use a different file.
        # But for now, let's just make sure we respect what's passed or what's expected.
        # If storage_service is mocked, load_data might return empty.
        # But in tests we are using real AppState which uses real StorageService by default.

        loaded_shapes, view_data = self.storage.load_data()
        self.shapes = loaded_shapes

        self.current_tool: ToolType = ToolType.HAND

        # Canvas transformation
        self.pan_x: float = view_data.get("pan_x", 0.0)
        self.pan_y: float = view_data.get("pan_y", 0.0)
        self.zoom: float = view_data.get("zoom", 1.0)

        # Theme
        self.theme_mode: str = "dark"  # 'dark' or 'light'
        self.is_shift_down: bool = False
        self.selected_polygon_type: str = "triangle"
        self.selected_line_type: str = "simple"

        # Side Rail & Drawer
        self.active_drawer_tab: Optional[str] = None  # None means closed

        self._listeners: List[Callable[[], None]] = []

        # Undo/Redo
        self.undo_stack: List[List[Shape]] = []
        self.redo_stack: List[List[Shape]] = []
        self._is_undoing_redoing: bool = False

        # Exporter
        self.exporter = Exporter()

        # Clipboard
        self.clipboard: List[dict] = []

    def add_listener(self, listener: Callable[[], None]):
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[], None]):
        if listener in self._listeners:
            self._listeners.remove(listener)

    def notify(self, save: bool = False):
        for listener in self._listeners:
            listener()
        if save:
            self.storage.save_data(self.shapes, self.pan_x, self.pan_y, self.zoom)

    def set_tool(self, tool: ToolType):
        self.current_tool = tool
        # Clear selection when switching to drawing tools
        if (
            tool != ToolType.SELECTION
            and tool != ToolType.HAND
            and tool != ToolType.BOX_SELECTION
        ):
            self.selected_shape_ids.clear()
        self.notify()

    def export_image(self, filename: str):
        # Ensure extension
        if not filename.lower().endswith(".png"):
            filename += ".png"

        # Export to data dir for now, or use absolute if provided?
        # Let's assume relative to CWD if no path given, or just use storage conventions.
        # But exporter handles paths.
        import os

        if not os.path.isabs(filename):
            # Default to "exports" folder
            filename = os.path.join("exports", filename)

        self.exporter.export_to_png(self.shapes, filename)

        if not self.selected_shape_ids:
            return

        self.clipboard.clear()
        for shape in self.shapes:
            if shape.id in self.selected_shape_ids:
                # Serialize and store
                serialized = self.storage._serialize_shape(shape)
                self.clipboard.append(serialized)

        # print(f"DEBUG: Copied {len(self.clipboard)} shapes to clipboard.")

    def paste(self):
        """
        Pastes shapes from the internal clipboard.
        Creates new instances, shifts them slightly, and selects them.
        """
        if not self.clipboard:
            return

        self.snapshot()  # Snapshot before adding new shapes

        new_selection_ids = []
        offset = 20  # Pixel offset for pasted items

        for shape_data in self.clipboard:
            # Deep copy the data
            import copy

            new_data = copy.deepcopy(shape_data)

            # Generate new ID
            import uuid

            new_data["id"] = str(uuid.uuid4())

            # Offset position
            new_data["x"] = new_data.get("x", 0) + offset
            new_data["y"] = new_data.get("y", 0) + offset

            # Handle specific properties that need offsetting
            type_ = new_data.get("type")
            if type_ == "line":
                new_data["end_x"] = new_data.get("end_x", 0) + offset
                new_data["end_y"] = new_data.get("end_y", 0) + offset
                # Clear connections on paste - typically we don't want to connect to original shapes
                new_data["start_shape_id"] = None
                new_data["end_shape_id"] = None

            elif type_ == "polygon" or type_ == "path":
                if "points" in new_data:
                    new_data["points"] = [
                        (p[0] + offset, p[1] + offset) for p in new_data["points"]
                    ]

            # Deserialize and add
            new_shape = self.storage._deserialize_shape(new_data)
            self.shapes.append(new_shape)
            new_selection_ids.append(new_shape.id)

        # Select pasted items
        self.selected_shape_ids.clear()
        self.selected_shape_ids.update(new_selection_ids)

        self.notify(save=True)
        # print(f"DEBUG: Pasted {len(new_selection_ids)} shapes.")

    def snapshot(self):
        """
        Saves the current state to the undo stack.
        Should be called BEFORE a destructive action.
        """
        if self._is_undoing_redoing:
            return

        # Deep copy is needed for undo/redo to work reliably
        # We can use serialization as a deep copy mechanism
        # Optimization: Only store necessary state
        current_state = [self.storage._serialize_shape(s) for s in self.shapes]

        # Limit stack size if needed (e.g. 50 steps)
        if len(self.undo_stack) >= 50:
            self.undo_stack.pop(0)

        self.undo_stack.append(current_state)
        self.redo_stack.clear()  # Clear redo stack on new action
        # print(f"DEBUG: Snapshot taken. Undo stack size: {len(self.undo_stack)}")

    def undo(self):
        if not self.undo_stack:
            return

        self._is_undoing_redoing = True
        try:
            # 1. Save current state to redo stack
            current_state = [self.storage._serialize_shape(s) for s in self.shapes]
            self.redo_stack.append(current_state)

            # 2. Pop from undo stack
            previous_state_data = self.undo_stack.pop()

            # 3. Restore state
            self.shapes = [
                self.storage._deserialize_shape(s) for s in previous_state_data
            ]

            # Clear selection to avoid selecting deleted shapes
            self.selected_shape_ids.clear()

            self.notify(save=True)
            # print(f"DEBUG: Undo performed. Undo stack: {len(self.undo_stack)}, Redo stack: {len(self.redo_stack)}")
        finally:
            self._is_undoing_redoing = False

    def redo(self):
        if not self.redo_stack:
            return

        self._is_undoing_redoing = True
        try:
            # 1. Save current state to undo stack
            current_state = [self.storage._serialize_shape(s) for s in self.shapes]
            self.undo_stack.append(current_state)

            # 2. Pop from redo stack
            next_state_data = self.redo_stack.pop()

            # 3. Restore state
            self.shapes = [self.storage._deserialize_shape(s) for s in next_state_data]

            # Clear selection
            self.selected_shape_ids.clear()

            self.notify(save=True)
            # print(f"DEBUG: Redo performed. Undo stack: {len(self.undo_stack)}, Redo stack: {len(self.redo_stack)}")
        finally:
            self._is_undoing_redoing = False

    def add_shape(self, shape: Shape):
        self.snapshot()
        self.shapes.append(shape)
        self.notify(save=True)

    def remove_shape(self, shape: Shape):
        if shape in self.shapes:
            self.snapshot()
            self.shapes.remove(shape)
            if shape.id in self.selected_shape_ids:
                self.selected_shape_ids.remove(shape.id)
            self.notify(save=True)

    def update_shape_position(
        self, shape: Shape, dx: float, dy: float, save: bool = True
    ):
        """
        Updates a shape's position and any connected lines.
        """
        # Update the shape itself
        shape.x += dx
        shape.y += dy

        if isinstance(shape, Line):
            shape.end_x += dx
            shape.end_y += dy
        elif isinstance(shape, Polygon):
            new_points = [(px + dx, py + dy) for px, py in shape.points]
            shape.points = new_points
        elif isinstance(shape, Group):
            # Recursively move children
            for child in shape.children:
                # We don't save intermediate steps
                # And we don't want to trigger recursive connected line updates for children here
                # effectively, because we might want the group to move as a unit.
                # But children might be lines connected to things OUTSIDE the group?
                # For now, let's just move the child geometry.
                self.update_shape_position(child, dx, dy, save=False)

        # Update connected lines
        self._update_connected_lines(shape, dx, dy)

        self.notify(save=save)

    def _update_connected_lines(
        self,
        moved_shape: Shape,
        dx: float,
        dy: float,
        moved_anchor_ids: Optional[set[str]] = None,
        caller_id: Optional[str] = None,
    ):
        """
        Finds all lines connected to moved_shape and updates their endpoints.

        Args:
            moved_shape: The shape that moved.
            dx: The amount moved in x.
            dy: The amount moved in y.
            moved_anchor_ids: A set of anchor IDs on moved_shape that actually moved.
                              If None, assumes the entire shape moved (all anchors).
            caller_id: The ID of the shape that triggered this update (to prevent cycles).
        """
        # print(f"DEBUG: _update_connected_lines for {moved_shape.id} delta=({dx},{dy}). Anchors: {moved_anchor_ids}")

        # 1. Update lines that are "children" of moved_shape (attached TO moved_shape)
        for s in self.shapes:
            if isinstance(s, Line):
                if s.id in self.selected_shape_ids:
                    continue

                # Prevent recursion if this child is the one who called us
                if caller_id and s.id == caller_id:
                    continue

                # Check connection to start
                if s.start_shape_id == moved_shape.id:
                    # Only update if the specific anchor moved, or if the whole shape moved
                    should_move = (
                        moved_anchor_ids is None
                        or s.start_anchor_id in moved_anchor_ids
                        or s.start_anchor_id
                        is None  # Handle generic connections as 'move with shape'
                    )

                    if should_move:
                        # print(f"DEBUG: Line {s.id} start connected to {moved_shape.id} anchor {s.start_anchor_id}. Moving start.")
                        s.x += dx
                        s.y += dy
                        # Recursive update: Line s only moved its start anchor ("start")
                        # Pass moved_shape.id as caller_id so s knows who moved it
                        self._update_connected_lines(
                            s,
                            dx,
                            dy,
                            moved_anchor_ids={"start"},
                            caller_id=moved_shape.id,
                        )

                # Check connection to end
                if s.end_shape_id == moved_shape.id:
                    should_move = (
                        moved_anchor_ids is None
                        or s.end_anchor_id in moved_anchor_ids
                        or s.end_anchor_id is None
                    )

                    if should_move:
                        # print(f"DEBUG: Line {s.id} end connected to {moved_shape.id} anchor {s.end_anchor_id}. Moving end.")
                        s.end_x += dx
                        s.end_y += dy
                        # Recursive update: Line s only moved its end anchor ("end")
                        self._update_connected_lines(
                            s,
                            dx,
                            dy,
                            moved_anchor_ids={"end"},
                            caller_id=moved_shape.id,
                        )

        # 2. Update lines that moved_shape is attached TO (Parent lines)
        if isinstance(moved_shape, Line):
            # Check Start Connection
            # Only update parent if:
            # a) We moved (so we pull parent)
            # b) We were NOT moved BY the parent (caller_id != parent.id)

            if moved_shape.start_shape_id and (
                moved_anchor_ids is None or "start" in moved_anchor_ids
            ):
                # Avoid cycle: If parent moved us, don't move parent back
                if not caller_id or caller_id != moved_shape.start_shape_id:
                    # If parent is also selected, it is moving on its own. Don't pull it.
                    if moved_shape.start_shape_id in self.selected_shape_ids:
                        pass
                    else:
                        parent = next(
                            (
                                s
                                for s in self.shapes
                                if s.id == moved_shape.start_shape_id
                            ),
                            None,
                        )
                        if parent and isinstance(parent, Line):
                            self._update_parent_anchor(
                                parent,
                                moved_shape.start_anchor_id,
                                dx,
                                dy,
                                child_id=moved_shape.id,
                            )

            # Check End Connection
            if moved_shape.end_shape_id and (
                moved_anchor_ids is None or "end" in moved_anchor_ids
            ):
                if not caller_id or caller_id != moved_shape.end_shape_id:
                    # If parent is also selected, it is moving on its own. Don't pull it.
                    if moved_shape.end_shape_id in self.selected_shape_ids:
                        pass
                    else:
                        parent = next(
                            (
                                s
                                for s in self.shapes
                                if s.id == moved_shape.end_shape_id
                            ),
                            None,
                        )
                        if parent and isinstance(parent, Line):
                            self._update_parent_anchor(
                                parent,
                                moved_shape.end_anchor_id,
                                dx,
                                dy,
                                child_id=moved_shape.id,
                            )

    def _update_parent_anchor(
        self, parent: Line, anchor_id: str, dx: float, dy: float, child_id: str
    ):
        """
        Updates a specific anchor on a parent line because a child attached to it moved.
        """
        if anchor_id == "start":
            parent.x += dx
            parent.y += dy
            # Recursively update things attached to parent's start
            # Pass child_id as caller_id so parent doesn't update child back
            self._update_connected_lines(
                parent, dx, dy, moved_anchor_ids={"start"}, caller_id=child_id
            )

        elif anchor_id == "end":
            parent.end_x += dx
            parent.end_y += dy
            self._update_connected_lines(
                parent, dx, dy, moved_anchor_ids={"end"}, caller_id=child_id
            )

    def update_shape(self, shape: Shape, save: bool = True):
        # Update connected lines if they are attached to anchors
        self._refresh_connected_lines(shape)
        self.notify(save=save)

    def _refresh_connected_lines(self, shape: Shape):
        """
        Updates endpoints of lines connected to 'shape' based on their anchor IDs.
        This allows lines to stay attached correctly when a shape is resized.
        """
        # We need to look for lines connected to this shape
        # and if they have an anchor_id, update their position.

        # Pre-calculate anchors for the shape to avoid re-calculating for every line
        anchors = shape.get_anchors()
        anchor_map = {a[0]: (a[1], a[2]) for a in anchors}
        # print(f"DEBUG: Refreshing lines for {shape.id} ({shape.type}). Anchors: {anchor_map}")

        for s in self.shapes:
            if isinstance(s, Line):
                # print(f"DEBUG: Checking line {s.id}. Start -> {s.start_shape_id}:{s.start_anchor_id}. End -> {s.end_shape_id}:{s.end_anchor_id}")

                # Check Start
                if s.start_shape_id == shape.id and s.start_anchor_id:
                    if s.start_anchor_id in anchor_map:
                        ax, ay = anchor_map[s.start_anchor_id]
                        # print(f"DEBUG: Updating line {s.id} start to {ax}, {ay}")
                        s.x = ax
                        s.y = ay
                        # Recursively update lines connected to this line's start
                        self._refresh_connected_lines(s)

                # Check End
                if s.end_shape_id == shape.id and s.end_anchor_id:
                    if s.end_anchor_id in anchor_map:
                        ax, ay = anchor_map[s.end_anchor_id]
                        # print(f"DEBUG: Updating line {s.id} end to {ax}, {ay}")
                        s.end_x = ax
                        s.end_y = ay
                        # Recursively update lines connected to this line's end
                        self._refresh_connected_lines(s)

    def select_shape(self, shape_id: Optional[str]):
        self.selected_shape_ids.clear()
        if shape_id:
            self.selected_shape_ids.add(shape_id)
        self.notify()

    def select_shapes(self, shape_ids: list[str]):
        self.selected_shape_ids.clear()
        self.selected_shape_ids.update(shape_ids)
        self.notify()

    @property
    def selected_shape_id(self) -> Optional[str]:
        # Backwards compatibility helper
        if len(self.selected_shape_ids) == 1:
            return list(self.selected_shape_ids)[0]
        return None

    def set_pan(self, x: float, y: float):
        self.pan_x = x
        self.pan_y = y
        self.notify(save=True)

    def set_zoom(self, zoom: float):
        self.zoom = zoom
        self.notify(save=True)

    def set_theme_mode(self, mode: str):
        self.theme_mode = mode
        self.notify()

    def set_polygon_type(self, polygon_type: str):
        self.selected_polygon_type = polygon_type
        self.notify()

    def set_line_type(self, line_type: str):
        self.selected_line_type = line_type
        self.notify()

    def set_shift_key(self, is_down: bool):
        if self.is_shift_down != is_down:
            self.is_shift_down = is_down
            # We don't necessarily need to notify/render on key press alone
            # unless it changes cursor or active drawing preview immediately.
            # But let's notify just in case UI needs to update.
            self.notify()

    def set_active_drawer_tab(self, tab_index: Optional[str]):
        """
        Set the active tab in the side rail.
        If the same tab is clicked, toggle it closed (set to None).
        """
        if self.active_drawer_tab == tab_index:
            self.active_drawer_tab = None
        else:
            self.active_drawer_tab = tab_index
        self.notify()

    def group_selection(self):
        if not self.selected_shape_ids or len(self.selected_shape_ids) < 2:
            return

        self.snapshot()

        # 1. Identify shapes to group
        shapes_to_group = []
        indices = []

        for i, shape in enumerate(self.shapes):
            if shape.id in self.selected_shape_ids:
                shapes_to_group.append(shape)
                indices.append(i)

        # 2. Sort by index to maintain relative order if needed, or just remove them
        # We need to remove them from self.shapes and add a new Group shape

        # Remove old shapes
        for shape in shapes_to_group:
            self.shapes.remove(shape)

        # 3. Create Group
        import uuid

        group = Group(id=str(uuid.uuid4()), type="group", children=shapes_to_group)

        # 4. Insert Group at the position of the top-most shape
        # We want the group to occupy the Z-index of the highest selected item.
        # Logic: max(indices) is the index of the top-most item to be grouped.
        # After removing all 'len(indices)' items, the slot where max(indices) was
        # shifts down by (len(indices) - 1).
        # Target index = max_index - (count_of_items_below_it_that_were_removed)
        # Since all other selected items are by definition below max_index (or at it),
        # count = len(indices) - 1.
        insert_idx = max(indices) - len(indices) + 1 if indices else len(self.shapes)

        # Remove old shapes
        for shape in shapes_to_group:
            self.shapes.remove(shape)

        self.shapes.insert(insert_idx, group)

        # 5. Update selection
        self.selected_shape_ids.clear()
        self.selected_shape_ids.add(group.id)

        self.notify(save=True)

    def ungroup_selection(self):
        if not self.selected_shape_ids:
            return

        # We can only ungroup if we selected groups
        groups_to_ungroup = []
        for shape in self.shapes:
            if shape.id in self.selected_shape_ids and isinstance(shape, Group):
                groups_to_ungroup.append(shape)

        if not groups_to_ungroup:
            return

        self.snapshot()

        new_selection = set()

        for group in groups_to_ungroup:
            # Remove group
            self.shapes.remove(group)

            # Add children back
            # We might want to adjust children's coordinates if group had its own x/y
            # But currently Group logic assumes children keep their world coordinates relative to 0,0
            # OR relative to group. For simplicity in MVP, let's say children store absolute world coords.
            # If we move group, we update children.

            for child in group.children:
                self.shapes.append(child)
                new_selection.add(child.id)

        self.selected_shape_ids = new_selection
        self.notify(save=True)

    def update_selected_shapes_properties(self, **properties):
        """
        Updates properties for all selected shapes.
        """
        if not self.selected_shape_ids:
            return

        # Snapshot before modification
        self.snapshot()

        updated = False
        for shape in self.shapes:
            if shape.id in self.selected_shape_ids:
                for key, value in properties.items():
                    if hasattr(shape, key):
                        setattr(shape, key, value)
                        updated = True

        if updated:
            self.notify(save=True)

    def move_shape_forward(self, shape_id: str):
        idx = -1
        for i, s in enumerate(self.shapes):
            if s.id == shape_id:
                idx = i
                break

        if idx != -1 and idx < len(self.shapes) - 1:
            self.snapshot()
            self.shapes[idx], self.shapes[idx + 1] = (
                self.shapes[idx + 1],
                self.shapes[idx],
            )
            self.notify(save=True)

    def move_shape_backward(self, shape_id: str):
        idx = -1
        for i, s in enumerate(self.shapes):
            if s.id == shape_id:
                idx = i
                break

        if idx > 0:
            self.snapshot()
            self.shapes[idx], self.shapes[idx - 1] = (
                self.shapes[idx - 1],
                self.shapes[idx],
            )
            self.notify(save=True)

    def close_drawer(self):
        self.active_drawer_tab = None
        self.notify()

    # File Management
    def list_files(self) -> List[str]:
        return self.storage.list_files()

    def list_folders(self) -> List[str]:
        return self.storage.list_folders()

    def get_current_filename(self) -> str:
        return self.storage.get_current_filename()

    def create_file(self, filename: str):
        if not filename.endswith(".json"):
            filename += ".json"
        # Save current state before switching
        self.storage.save_data(
            self.shapes, self.pan_x, self.pan_y, self.zoom, immediate=True
        )
        self.storage.create_file(filename)
        self.switch_file(filename)

    def create_folder(self, folder_name: str):
        self.storage.create_folder(folder_name)
        self.notify()

    def switch_file(self, filename: str):
        # Save current state before switching
        # We check if we are already on this file to avoid redundant saves/reloads,
        # but switch_file logic usually implies a change.
        if self.get_current_filename() != filename:
            self.storage.save_data(
                self.shapes, self.pan_x, self.pan_y, self.zoom, immediate=True
            )

        self.storage.switch_file(filename)
        self._reload_from_storage()

    def delete_file(self, filename: str):
        current_before = self.get_current_filename()
        self.storage.delete_file(filename)
        current_after = self.get_current_filename()

        # If the underlying storage switched files (because we deleted the current one), reload.
        if current_before != current_after or filename == current_before:
            self._reload_from_storage()
        else:
            # Just notify so the file list updates
            self.notify()

    def delete_folder(self, folder_name: str):
        current_before = self.get_current_filename()
        self.storage.delete_folder(folder_name)
        current_after = self.get_current_filename()

        if current_before != current_after:
            self._reload_from_storage()
        else:
            self.notify()

    def _reload_from_storage(self):
        self.shapes, view_data = self.storage.load_data()
        self.pan_x = view_data.get("pan_x", 0.0)
        self.pan_y = view_data.get("pan_y", 0.0)
        self.zoom = view_data.get("zoom", 1.0)
        self.selected_shape_ids.clear()
        self.notify()
