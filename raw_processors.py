"""
Examples
--------

Create raw filtering chain

>>> rd, wrt = FifReader(), MneWriter()
>>> flt = BandPassFilter(config = {"l_freq": 1, "h_freq": 100})
>>> filt_chain = RawProcessorsChain(["i.fif"], "o.fif", rd, [flt], wrt)
>>> print(filt_chain.processors)
[BandPassFilter(config={'l_freq': 1, 'h_freq': 100})]

Create raw chain filtering and resampling

>>> rd, wrt = FifReader(), MneWriter()
>>> flt = BandPassFilter(config = {"l_freq": 1, "h_freq": 100})
>>> rsmp = Resample()
>>> filt_chain = RawProcessorsChain(["i.fif"], "o.fif", rd, [flt, rsmp], wrt)
>>> print(filt_chain.processors)
[BandPassFilter(config={'l_freq': 1, 'h_freq': 100}), Resample(config={})]

"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from os import PathLike
from typing import Union
from collections.abc import Collection

from mne import concatenate_raws
from mne.io import Raw, read_raw_fif
from mne.io.base import BaseRaw

from nodes import FileIoNode


class RawProcessor(ABC):
    @abstractmethod
    def run(self, raw_input: Union[BaseRaw, Collection[BaseRaw]]) -> BaseRaw:
        """Run processor"""


@dataclass
class BandPassFilter(RawProcessor):
    config: dict = field(default_factory=lambda: dict(l_freq=1, h_freq=100))

    def run(self, raw: BaseRaw) -> BaseRaw:
        return raw.copy().filter(**self.config)


class ConcatRaws(RawProcessor):
    """Concatenate common channels from raw objects"""

    def run(self, *raws: Collection[BaseRaw]) -> BaseRaw:
        if len(raws) == 1:
            return raws[0]
        raws_cp = self._intersect_chs(raws)
        return concatenate_raws(raws_cp)

    def _intersect_chs(self, raws: Collection[BaseRaw]) -> Collection[BaseRaw]:
        raws_cp = [r.copy() for r in raws]
        common_ch_names = set.intersection(*[set(r.ch_names) for r in raws_cp])
        for raw in raws_cp:
            raw.pick_channels(list(common_ch_names))
        return raws_cp


@dataclass
class Resample(RawProcessor):
    config: dict = field(default_factory=dict)

    def run(self, raw: BaseRaw) -> BaseRaw:
        return raw.copy().resample(**self.config)


@dataclass
class RawReader(ABC):
    config: dict

    @abstractmethod
    def read(self, path) -> BaseRaw:
        """Read in raw data"""


@dataclass
class FifReader(RawReader):
    config: dict = field(default_factory=lambda: dict(preload=True))

    def read(self, path: PathLike) -> Raw:
        return read_raw_fif(path, **self.config)


@dataclass
class RawWriter(ABC):
    config: dict

    @abstractmethod
    def write(self, raw: BaseRaw, path: PathLike):
        """Write raw data to a filesystem"""


@dataclass
class MneWriter(RawWriter):
    config: dict = field(default_factory=dict)

    def write(self, raw: BaseRaw, path: PathLike):
        raw.save(path, **self.config)


@dataclass
class MneBidsWriter(RawWriter):
    """Write raw file together with BIDS metainfo"""


@dataclass
class RawProcessorsChain(FileIoNode):
    """
    Read multiple raw objects, process them into one raw object and write

    """

    raw_in_paths: Collection[PathLike]
    raw_out_path: PathLike
    reader: RawReader
    processors: Collection[RawProcessor]
    writer: RawWriter

    def _read_input(self):
        return [self.reader.read(p) for p in self.raw_in_paths]

    def _write_output(self, result):
        self.writer.write(result, self.raw_out_path)

    def _process(self, in_objs):
        return self._run_processors(in_objs)

    def _run_processors(self, in_objs):
        assert self.processors, "Must pass at least one processor"
        intermediate_raw = self.processors[0].run(*in_objs)
        for node in self.processors[1:]:
            intermediate_raw = node.run(intermediate_raw)
        return intermediate_raw


def main():
    import doctest

    doctest.testmod()


if __name__ == "__main__":
    main()
