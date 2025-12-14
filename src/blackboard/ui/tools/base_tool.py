from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..canvas import BlackboardCanvas


class BaseTool(ABC):
    def __init__(self, canvas: "BlackboardCanvas"):
        self.canvas = canvas
        self.app_state = canvas.app_state

    @abstractmethod
    def on_down(self, x: float, y: float, e):
        """Handle mouse down / pan start event."""
        pass

    @abstractmethod
    def on_move(self, x: float, y: float, e):
        """Handle mouse move / pan update event."""
        pass

    @abstractmethod
    def on_up(self, x: float, y: float, e):
        """Handle mouse up / pan end event."""
        pass

    def on_click(self, x: float, y: float, e):
        """Optional: Handle immediate click without drag."""
        pass

    def draw_overlays(self, overlay_shapes: list):
        """Optional: Add tool-specific shapes to the overlay layer."""
        pass
