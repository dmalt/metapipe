from abc import ABC, abstractmethod
from os import PathLike
from typing import Any, Sequence, Union, NamedTuple

from mne import Epochs  # type: ignore
from mne.io.base import BaseRaw  # type: ignore

MneContainer = Union[BaseRaw, Epochs]


class FileProcessor(ABC):
    @staticmethod
    @abstractmethod
    def InPaths(*pargs, **kwargs) -> NamedTuple:
        """
        Input specification for run()

        Should be defined as a NamedTuple subclass

        """

    @staticmethod
    @abstractmethod
    def OutPaths(*pargs, **kwargs) -> NamedTuple:
        """
        Output specification for run()

        Should be defined as a NamedTuple subclass

        """

    def run(self, deps: NamedTuple, target: NamedTuple) -> None:
        """Read data, process it and save the result"""
        in_objs = self._read_input(deps)
        result = self._process(in_objs)
        self._write_output(result, target)

    @abstractmethod
    def _read_input(self, deps) -> Sequence[Any]:
        """Read input files"""

    @abstractmethod
    def _process(self, in_objs: Sequence[Any]) -> Any:
        """Process read-in objects"""

    @abstractmethod
    def _write_output(self, result: Any, targets) -> None:
        """Write the result to filesystem"""

    def make_task(self, name, deps: NamedTuple, targets: NamedTuple) -> dict:
        """Produce doit task"""
        return dict(
            name=name,
            file_dep=list(deps),
            actions=[(self.run, [deps, targets])],
            targets=list(targets),
            clean=True,
        )


class ConfigurableFileProcessor(FileProcessor):
    config: dict

    def make_task(self, name, deps: NamedTuple, targets: NamedTuple) -> dict:
        from doit.tools import config_changed  # type: ignore

        base_dict = super().make_task(name, deps, targets)
        base_dict["uptodate"] = [config_changed(self.config)]
        return base_dict


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
