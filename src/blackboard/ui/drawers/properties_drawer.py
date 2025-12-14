import flet as ft
from .base_drawer import BaseDrawer
from ...state.app_state import AppState


class PropertiesDrawer(BaseDrawer):
    def __init__(self, app_state: AppState):
        super().__init__(app_state)

    def _get_properties_content(self) -> list[ft.Control]:
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

        # If we selected a group, finding it might be tricky if shapes list only has top-level?
        # AppState.shapes should have all shapes if flat, or top level if tree.
        # Assuming flat for simple search, or we need recursive search if groups exist.
        # However, app_state.shapes usually stores everything or we rely on ID lookup.
        # Let's verify how we find the shape.
        # Original code:
        # for s in self.app_state.shapes:
        #    if s.id in list(selected_ids)[0]: ...
        # Wait, selected_ids is a set of IDs. list(selected_ids)[0] gives one ID.
        # But `s.id in ...` check seems weird if `s.id` is string and list[0] is string.
        # It should be `if s.id == ...`?
        # Let's stick to the original logic pattern but fix if it looks like a bug or just copy.
        # Original: if s.id in list(selected_ids)[0]:
        # If selected_ids is {'abc'}, list is ['abc'], [0] is 'abc'.
        # 'abc' in 'abc' is True. 'a' in 'abc' is True.
        # This seems dangerously loose if IDs are subsets of each other, but let's replicate logic for now or improve.
        # Actually, let's improve to strict equality if we are sure.
        # The original code was:
        # for s in self.app_state.shapes:
        #     if s.id in list(selected_ids)[0]:
        #         first_shape = s
        #         break
        # This looks like it meant `s.id == list(selected_ids)[0]`.

        target_id = list(selected_ids)[0]
        first_shape = next(
            (s for s in self.app_state.shapes if s.id == target_id), None
        )

        if not first_shape:
            # Fallback for nested shapes if not found in top level (if supported)
            # For now return error content
            return [
                ft.Text("Properties", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("Selection details not available", italic=True),
            ]

        # Check for grouping capabilities
        can_group = len(selected_ids) > 1
        can_ungroup = False
        for s in self.app_state.shapes:
            if s.id in selected_ids and s.type == "group":
                can_ungroup = True
                break

        def on_group_click(_):
            self.app_state.group_selection()

        def on_ungroup_click(_):
            self.app_state.ungroup_selection()

        def on_stroke_width_change(e):
            self.app_state.update_selected_shapes_properties(
                stroke_width=float(e.control.value)
            )

        def on_opacity_change(e):
            self.app_state.update_selected_shapes_properties(
                opacity=float(e.control.value) / 100
            )

        def on_stroke_color_change(color):
            self.app_state.update_selected_shapes_properties(stroke_color=color)

        def on_fill_color_change(color):
            if color == "transparent":
                self.app_state.update_selected_shapes_properties(
                    fill_color="transparent", filled=False
                )
            else:
                self.app_state.update_selected_shapes_properties(
                    fill_color=color, filled=True
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

        def on_stroke_join_change(e):
            self.app_state.update_selected_shapes_properties(
                stroke_join=e.control.value.lower()
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
                create_color_swatch(
                    c,
                    first_shape.stroke_color,
                    lambda _, color=c: on_stroke_color_change(color),
                )
            )

        # Fill Color Swatches
        fill_swatches = ft.Row(wrap=True, spacing=5)
        for c in colors:
            fill_swatches.controls.append(
                create_color_swatch(
                    c,
                    first_shape.fill_color,
                    lambda _, color=c: on_fill_color_change(color),
                )
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
            ft.Row(
                [
                    ft.ElevatedButton(
                        "Group",
                        icon=ft.Icons.GROUP_WORK,
                        on_click=on_group_click,
                        disabled=not can_group,
                    ),
                    ft.ElevatedButton(
                        "Ungroup",
                        icon=ft.Icons.GROUP_OFF,
                        on_click=on_ungroup_click,
                        disabled=not can_ungroup,
                    ),
                ]
            ),
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
            ft.Text("Corner Style"),
            ft.Dropdown(
                value=getattr(first_shape, "stroke_join", "miter").capitalize(),
                options=[
                    ft.dropdown.Option("Miter"),
                    ft.dropdown.Option("Round"),
                    ft.dropdown.Option("Bevel"),
                ],
                on_change=on_stroke_join_change,
            ),
            ft.Container(height=10),
            ft.Text("Fill Color"),
            fill_swatches,
        ]

    def build(self) -> list[ft.Control]:
        return self._get_properties_content()
