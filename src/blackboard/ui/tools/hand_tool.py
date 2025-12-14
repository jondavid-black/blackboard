from .base_tool import BaseTool


class HandTool(BaseTool):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.start_pan_x = 0
        self.start_pan_y = 0
        self.initial_pan_x = 0
        self.initial_pan_y = 0

    def on_down(self, x: float, y: float, e):
        # We use screen coordinates (e.local_x/y) for panning physics
        self.start_pan_x = e.local_x
        self.start_pan_y = e.local_y
        self.initial_pan_x = self.app_state.pan_x
        self.initial_pan_y = self.app_state.pan_y

    def on_move(self, x: float, y: float, e):
        dx = e.local_x - self.start_pan_x
        dy = e.local_y - self.start_pan_y
        self.app_state.set_pan(self.initial_pan_x + dx, self.initial_pan_y + dy)

    def on_up(self, x: float, y: float, e):
        pass
