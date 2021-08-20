from abc import ABC, abstractmethod
from typing import Any, Sequence


class FileIoNode(ABC):
    def run(self) -> Any:
        """Read data, process it and save the result"""
        in_objs = self._read_input()
        result = self._process(in_objs)
        self._write_output(result)

    @abstractmethod
    def _read_input(self) -> Sequence[Any]:
        """Read input files"""

    @abstractmethod
    def _process(self, in_objs: Sequence[Any]) -> Any:
        """Process read-in objects"""

    @abstractmethod
    def _write_output(self, result: Any) -> None:
        """Write the result to filesystem"""