import flet as ft
from abc import ABC, abstractmethod
from ...state.app_state import AppState


class BaseDrawer(ABC):
    def __init__(self, app_state: AppState):
        self.app_state = app_state

    @abstractmethod
    def build(self) -> list[ft.Control]:
        """Return the list of controls for this drawer."""
        pass

    def update(self):
        """
        Optional method to handle updates if the drawer keeps references to controls.
        Since we regenerate content on state change usually, this might not be needed
        unless we move to a stateful widget approach.
        """
        pass
