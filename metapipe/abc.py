from abc import ABC, abstractmethod
from os import PathLike
from typing import Any, Sequence, Union

from mne import Epochs  # type: ignore
from mne.io.base import BaseRaw  # type: ignore

MneContainer = Union[BaseRaw, Epochs]


class FileProcessor(ABC):
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


class InMemoProcessor(ABC):
    """Type-preserving in-memory processor abstraction"""
    @abstractmethod
    def run(self, in_obj: Any) -> Any:
        """Run processor"""


class Reader(ABC):
    config: dict

    @abstractmethod
    def read(self, path: PathLike) -> Any:
        """Read in raw data"""


class Writer(ABC):
    config: dict

    @abstractmethod
    def write(self, data: Any, path: PathLike) -> None:
        """Write raw data to a filesystem"""
