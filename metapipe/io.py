from dataclasses import dataclass, field
from os import PathLike

from mne.io import Raw, read_raw_fif  # type: ignore
from mne.io.base import BaseRaw

from metapipe.interfaces import Reader, Writer


@dataclass
class RawFifReader(Reader):
    config: dict = field(default_factory=lambda: dict(preload=True))

    def read(self, path: PathLike) -> Raw:
        return read_raw_fif(path, **self.config)


@dataclass
class MneWriter(Writer):
    config: dict = field(default_factory=dict)

    def write(self, raw: BaseRaw, path: PathLike) -> None:
        raw.save(path, **self.config)


class MneBidsWriter(Writer):
    """Write raw file together with BIDS metainfo"""
