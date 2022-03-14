from abc import abstractmethod
from os import PathLike
from typing import Any, Protocol, Union

from mne import Epochs  # type: ignore
from mne.io.base import BaseRaw  # type: ignore

MneContainer = Union[BaseRaw, Epochs]


class Processor(Protocol):
    def run(self, data: Any) -> Any:
        """Process data"""


class Reader(Protocol):
    @abstractmethod
    def run(self, path: PathLike) -> Any:
        """Read in data"""


class Writer(Protocol):
    @abstractmethod
    def run(self, savepath: PathLike, data: Any) -> None:
        """Write data to a filesystem"""
