import flet as ft
from blackboard.state.app_state import AppState
import math
import flet.canvas as cv


class Background(ft.Stack):
    def __init__(self, app_state: AppState):
        self.app_state = app_state
        self.grid_canvas = cv.Canvas(expand=True)
        # Background color container
        self.bg_container = ft.Container(
            expand=True,
            bgcolor=self._get_color(),
        )
        super().__init__(
            expand=True,
            controls=[self.bg_container, self.grid_canvas],
        )

    def did_mount(self):
        self.app_state.add_listener(self._on_state_change)
        # Trigger initial draw if page is available (it should be)
        if self.page:
            self._draw_grid()

    def will_unmount(self):
        self.app_state.remove_listener(self._on_state_change)

    def _on_state_change(self):
        self.bg_container.bgcolor = self._get_color()
        self._draw_grid()
        self.update()

    def _get_color(self):
        return (
            ft.Colors.BLUE_GREY_900
            if self.app_state.theme_mode == "dark"
            else ft.Colors.WHITE
        )

    def _draw_grid(self):
        self.grid_canvas.shapes.clear()

        grid_type = self.app_state.grid_type
        if grid_type == "none":
            self.grid_canvas.update()
            return

        # Grid parameters
        base_spacing = 40.0  # World units

        # View parameters
        zoom = self.app_state.zoom
        pan_x = self.app_state.pan_x
        pan_y = self.app_state.pan_y

        # Adaptive Grid Logic
        # We want the screen spacing to stay within a comfortable range.
        # Increased minimum spacing to improve performance (especially for dots).
        min_screen_spacing = 50.0

        current_screen_spacing = base_spacing * zoom

        step_multiplier = 1.0
        if current_screen_spacing < min_screen_spacing:
            while (base_spacing * step_multiplier * zoom) < min_screen_spacing:
                step_multiplier *= 2
        elif current_screen_spacing > (min_screen_spacing * 2):
            # We want to subdivide as soon as we have enough space for 2 intervals
            # i.e., if we have > 100px, we can split to 50px.
            while (base_spacing * step_multiplier * zoom) > (min_screen_spacing * 2):
                step_multiplier /= 2

        effective_spacing = base_spacing * step_multiplier

        # Color settings
        is_dark = self.app_state.theme_mode == "dark"
        color = ft.Colors.WHITE24 if is_dark else ft.Colors.BLACK12

        # We need screen dimensions to know how many lines to draw.
        # If page is not ready, we can't draw effectively.
        if not self.page:
            return

        width = self.page.width
        height = self.page.height

        # Calculate visible range in world coordinates
        # Screen (0,0) -> World (-pan_x/zoom, -pan_y/zoom)

        # We align to effective_spacing
        start_col = math.floor((-pan_x) / (zoom * effective_spacing))
        end_col = math.ceil((width - pan_x) / (zoom * effective_spacing))

        start_row = math.floor((-pan_y) / (zoom * effective_spacing))
        end_row = math.ceil((height - pan_y) / (zoom * effective_spacing))

        # Limit grid drawing just in case, but adaptive spacing should prevent this
        max_lines = 1000  # Increased safety limit since density is controlled
        if (end_col - start_col) > max_lines or (end_row - start_row) > max_lines:
            pass
        else:
            if grid_type == "line":
                stroke_width = 1

                # Draw vertical lines
                for col in range(start_col, end_col + 1):
                    x_world = col * effective_spacing
                    x_screen = x_world * zoom + pan_x
                    self.grid_canvas.shapes.append(
                        cv.Line(
                            x_screen,
                            0,
                            x_screen,
                            height,
                            paint=ft.Paint(stroke_width=stroke_width, color=color),
                        )
                    )

                # Draw horizontal lines
                for row in range(start_row, end_row + 1):
                    y_world = row * effective_spacing
                    y_screen = y_world * zoom + pan_y
                    self.grid_canvas.shapes.append(
                        cv.Line(
                            0,
                            y_screen,
                            width,
                            y_screen,
                            paint=ft.Paint(stroke_width=stroke_width, color=color),
                        )
                    )

            elif grid_type == "dot":
                radius = 2

                for col in range(start_col, end_col + 1):
                    for row in range(start_row, end_row + 1):
                        x_world = col * effective_spacing
                        y_world = row * effective_spacing

                        x_screen = x_world * zoom + pan_x
                        y_screen = y_world * zoom + pan_y

                        self.grid_canvas.shapes.append(
                            cv.Circle(
                                x_screen,
                                y_screen,
                                radius,
                                paint=ft.Paint(
                                    color=color, style=ft.PaintingStyle.FILL
                                ),
                            )
                        )

        self.grid_canvas.update()
