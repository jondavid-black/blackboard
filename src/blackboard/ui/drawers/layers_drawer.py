import flet as ft
from typing import List
from .base_drawer import BaseDrawer
from ...state.app_state import AppState
from ...models import Shape, Group


class LayersDrawer(BaseDrawer):
    def __init__(self, app_state: AppState):
        super().__init__(app_state)

    def build(self) -> list[ft.Control]:
        return [
            ft.Container(
                content=ft.Column(
                    controls=self._get_layers_content(),
                    expand=True,
                ),
                padding=10,
                expand=True,
            )
        ]

    def _get_layers_content(self) -> list[ft.Control]:
        # The test expects [Title, Divider, ScrollableColumn]

        # Build the tree of shapes
        layer_controls = self._build_layer_tree(self.app_state.shapes, depth=0)

        # Add a "Bottom" drop target at the end to allow dragging to the bottom of the list
        layer_controls.append(self._create_bottom_drop_target())

        return [
            ft.Text("Layers", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Column(
                controls=layer_controls,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
        ]

    def _build_layer_tree(self, shapes: List[Shape], depth: int) -> List[ft.Control]:
        controls = []
        # Iterate in reverse so top-most shapes are at the top of the list
        for shape in reversed(shapes):
            controls.append(self._create_layer_item(shape, depth))

            # If it's a group, recursively add children
            if isinstance(shape, Group):
                # Always show the group item itself
                # Check expansion state
                is_expanded = shape.id in self.app_state.expanded_group_ids
                if is_expanded:
                    children_controls = self._build_layer_tree(
                        shape.children, depth + 1
                    )
                    controls.extend(children_controls)

        return controls

    def _create_layer_item(self, shape: Shape, depth: int) -> ft.Control:
        is_selected = shape.id in self.app_state.selected_shape_ids

        # Indentation
        padding_left = depth * 20

        # Visual content
        icon = ft.Icons.INSERT_DRIVE_FILE
        if isinstance(shape, Group):
            is_expanded = shape.id in self.app_state.expanded_group_ids
            icon = ft.Icons.FOLDER_OPEN if is_expanded else ft.Icons.FOLDER

        content = ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.KEYBOARD_ARROW_DOWN
                        if shape.id in self.app_state.expanded_group_ids
                        else ft.Icons.KEYBOARD_ARROW_RIGHT,
                        icon_size=16,
                        visible=isinstance(shape, Group),
                        on_click=lambda e,
                        s=shape: self.app_state.toggle_group_expansion(s.id),
                    ),
                    ft.Icon(
                        icon,
                        size=16,
                        color=ft.Colors.BLUE if isinstance(shape, Group) else None,
                    ),
                    ft.Text(f"{shape.type} {shape.id[:4]}", size=14, expand=True),
                    ft.IconButton(
                        ft.Icons.VISIBILITY
                        if shape.opacity > 0
                        else ft.Icons.VISIBILITY_OFF,
                        icon_size=16,
                        on_click=lambda e, s=shape: self._toggle_visibility(s),
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE)
            if is_selected
            else None,
            padding=ft.padding.only(left=padding_left, right=10, top=5, bottom=5),
            border_radius=5,
            on_click=lambda e, s=shape: self.app_state.select_shape(s.id),
        )

        # Drag wrapper
        draggable = ft.Draggable(
            group="layer",
            content=content,
            content_feedback=ft.Container(
                content=ft.Text(
                    f"Moving {shape.type}...", size=14, color=ft.Colors.WHITE
                ),
                bgcolor=ft.Colors.BLUE,
                padding=1,
                border_radius=5,
                opacity=0.8,
            ),
            data=shape.id,
        )

        # Drop wrapper (DragTarget)
        drag_target = ft.DragTarget(
            group="layer",
            content=draggable,
            on_accept=lambda e, target_id=shape.id: self._on_layer_drop(e, target_id),
            data=shape.id,  # Store ID for testing inspection if needed
        )

        return drag_target

    def _create_bottom_drop_target(self) -> ft.Control:
        return ft.DragTarget(
            group="layer",
            content=ft.Text(
                "Drop here to place at the bottom", size=14, color=ft.Colors.GREY
            ),
            on_accept=lambda e: self._on_layer_drop(e, "__BOTTOM__"),
            data="__BOTTOM__",
        )

    def _start_drag(self, shape_id: str):
        self.app_state.select_shape(shape_id)

    def _on_layer_drop(self, e: ft.DragTargetEvent, target_id: str):
        moved_shape_id = self.app_state.selected_shape_id

        if not moved_shape_id:
            return

        if target_id == "__BOTTOM__":
            self.app_state.move_shape_to_root_end(moved_shape_id)
            return

        # Check if target is a group and if it's expanded

        # Helper to find shape type/expansion status
        is_expanded_group = target_id in self.app_state.expanded_group_ids

        # We need to know if target_id refers to a Group.
        # Since we don't have the object easily here without searching,
        # let's assume we can rely on AppState or search quickly.
        # Or, we can let AppState handle the decision?
        # No, AppState doesn't know about UI expansion state implicitly for logic (it stores it but logically reorder doesn't care).
        # We should make the decision here.

        # Let's verify if it's a group.
        # Since finding it recursively is cheap for small lists:
        target_list, target_idx = self.app_state._find_shape_location(target_id)
        if (
            target_list
            and isinstance(target_list[target_idx], Group)
            and is_expanded_group
        ):
            self.app_state.move_shape_into_group(moved_shape_id, target_id)
        else:
            self.app_state.reorder_shape(moved_shape_id, target_id)

    def _toggle_visibility(self, shape: Shape):
        # Toggle opacity for now
        shape.opacity = 0.0 if shape.opacity > 0 else 1.0
        self.app_state.notify(save=True)
