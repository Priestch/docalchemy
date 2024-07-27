from typing import TYPE_CHECKING
from .services import FurnaceService

if TYPE_CHECKING:
    pass


class Furnace:
    def __init__(self, service: FurnaceService):
        self.service = service

    def start(self):
        """Start the doc furnace
        :return: None
        """
        print("start")

    def stop(self):
        """Stop the doc furnace
        :return: None
        """
        print("stop")
