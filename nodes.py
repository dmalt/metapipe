from abc import ABC, abstractmethod
from collections.abc import Collection
from typing import Any


class FileIoNode(ABC):
    def run(self):
        """Read data, process it and save the result"""
        in_objs = self._read_input()
        result = self._process(in_objs)
        self._write_output(result)

    @abstractmethod
    def _read_input(self) -> Collection[Any]:
        """Read input files"""

    @abstractmethod
    def _process(self, in_objs) -> Any:
        """Process read-in objects"""

    @abstractmethod
    def _write_output(self, result):
        """Write the result to filesystem"""
