from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from os import PathLike
from typing import (
    Any,
    Sequence,
    Union,
    List,
    Protocol,
    NamedTuple,
    TypeVar,
    Generic,
    Type
)


from mne import Epochs  # type: ignore
from mne.io.base import BaseRaw  # type: ignore

MneContainer = Union[BaseRaw, Epochs]


class BuilderNotReadyError(Exception):
    pass


@dataclass  # type: ignore
class BaseBuilder(ABC):
    _deps: dict = field(init=False, repr=False, default_factory=dict)
    _targets: dict = field(init=False, repr=False, default_factory=dict)

    @abstractmethod
    def with_deps(self, *p, **kw) -> "BaseBuilder":
        """Set dependency paths"""

    @abstractmethod
    def with_targets(self, *p, **kw) -> "BaseBuilder":
        """Set target paths"""

    @abstractmethod
    def build(self) -> "FileProcessor":
        """Build an object"""

    @property
    def deps(self):
        return sorted(self._deps.values())

    @property
    def targets(self):
        return sorted(self._targets.values())

    def is_ready(self):
        try:
            self.check_ready()
            return True
        except BuilderNotReadyError:
            return False

    def check_ready(self) -> None:
        if not self._deps:
            raise BuilderNotReadyError("Dependencies are not set")
        if not self._targets:
            raise BuilderNotReadyError("Targets are not set")


@dataclass  # type: ignore
class FileProcessor(ABC):
    _deps: dict
    _targets: dict

    @property
    def deps(self) -> List[PathLike]:
        return sorted(self._deps.values())

    @property
    def targets(self) -> List[PathLike]:
        return sorted(self._targets.values())

    @property
    @abstractmethod
    def Builder(self) -> BaseBuilder:
        """Builder class"""

    def run(self) -> None:
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


T = TypeVar("T", bound=NamedTuple)


class Processor(Generic[T], Protocol):
    OutSpec: Type[T]

    @abstractmethod
    def run(self, data: Any) -> T:
        """Process data"""


class Reader(Generic[T], Protocol):
    OutSpec: Type[T]

    @abstractmethod
    def run(self) -> T:
        """Read in data"""


class Writer(Protocol):
    @abstractmethod
    def run(self, data: Any) -> None:
        """Write data to a filesystem"""
