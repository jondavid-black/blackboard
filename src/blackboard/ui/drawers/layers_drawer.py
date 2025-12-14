import flet as ft
from .base_drawer import BaseDrawer
from ...state.app_state import AppState


class LayersDrawer(BaseDrawer):
    def __init__(self, app_state: AppState):
        super().__init__(app_state)

    def _on_layer_drop(self, e):
        src_id = e.data
        target_id = e.control.data  # The ID of the shape we dropped ONTO

        if not src_id or not target_id:
            return

        # Clean up potential prefixes
        if src_id.startswith("drag_"):
            src_id = src_id.replace("drag_", "")

        if target_id == "__BOTTOM__":
            self.app_state.move_shape_to_back(src_id)
            return

        if src_id == target_id:
            return

        self.app_state.reorder_shape(src_id, target_id)

    def _start_drag(self, shape_id):
        # Optional: could trigger visual feedback
        pass

    def _get_layers_content(self) -> list[ft.Control]:
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
                            ft.IconButton(
                                ft.Icons.VERTICAL_ALIGN_TOP,
                                icon_size=14,
                                tooltip="Move to Front",
                                on_click=lambda _,
                                s=shape.id: self.app_state.move_shape_to_front(s),
                            ),
                            ft.IconButton(
                                ft.Icons.VERTICAL_ALIGN_BOTTOM,
                                icon_size=14,
                                tooltip="Move to Back",
                                on_click=lambda _,
                                s=shape.id: self.app_state.move_shape_to_back(s),
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
                    on_long_press=lambda _, s=shape.id: self._start_drag(s),
                    data=shape.id,
                )
            )

            draggable = ft.Draggable(
                group="layer",
                content=layer_controls[-1],
                content_when_dragging=ft.Container(
                    content=ft.Text(f"Moving {shape.type}...", color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.BLUE_GREY_400,
                    padding=5,
                    border_radius=5,
                    opacity=0.5,
                ),
                data=shape.id,
            )

            drag_target = ft.DragTarget(
                group="layer",
                content=draggable,
                on_accept=self._on_layer_drop,
                data=shape.id,
            )

            layer_controls[-1] = drag_target

        # Add a drop target for the bottom of the list
        layer_controls.append(
            ft.DragTarget(
                group="layer",
                content=ft.Container(
                    height=40,
                    bgcolor=ft.Colors.TRANSPARENT,
                    alignment=ft.alignment.center,
                    content=ft.Text(
                        "Drop here to move to back",
                        size=10,
                        color=ft.Colors.GREY_400,
                        italic=True,
                    ),
                    border=ft.border.all(1, ft.Colors.TRANSPARENT),
                ),
                on_accept=self._on_layer_drop,
                data="__BOTTOM__",
            )
        )

        return [
            ft.Text("Layers", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Column(controls=layer_controls, scroll=ft.ScrollMode.AUTO, expand=True),
        ]

    def build(self) -> list[ft.Control]:
        return self._get_layers_content()
