from abc import ABC, abstractmethod
from os import PathLike
from typing import Union, Any, Sequence, Collection
from mne.io.base import BaseRaw  # type: ignore


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


class RawProcessor(ABC):
    @abstractmethod
    def run(self, raw_input: Union[BaseRaw, Collection[BaseRaw]]) -> BaseRaw:
        """Run processor"""


class RawReader(ABC):
    config: dict

    @abstractmethod
    def read(self, path: PathLike) -> BaseRaw:
        """Read in raw data"""


class RawWriter(ABC):
    config: dict

    @abstractmethod
    def write(self, raw: BaseRaw, path: PathLike) -> None:
        """Write raw data to a filesystem"""
