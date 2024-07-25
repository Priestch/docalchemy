from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litestar.stores.file import FileStore


class Furnace:
    def __init__(self, storage: FileStore):
        self.storage = storage

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
