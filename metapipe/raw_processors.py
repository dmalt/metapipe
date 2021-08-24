"""
Examples
--------

Create raw filtering chain

>>> rd, wrt = RawFifReader(), MneWriter()
>>> flt = BandPassFilter(config = {"l_freq": 1, "h_freq": 100})
>>> filt_chain = RawProcessorsChain(["i.fif"], "o.fif", rd, [flt], wrt)
>>> print(filt_chain.processors)
[BandPassFilter(config={'l_freq': 1, 'h_freq': 100})]

Create raw chain filtering and resampling

>>> rd, wrt = RawFifReader(), MneWriter()
>>> flt = BandPassFilter(config = {"l_freq": 1, "h_freq": 100})
>>> rsmp = Resample()
>>> filt_chain = RawProcessorsChain(["i.fif"], "o.fif", rd, [flt, rsmp], wrt)
>>> print(filt_chain.processors)
[BandPassFilter(config={'l_freq': 1, 'h_freq': 100}), Resample(config={})]

"""

from dataclasses import dataclass, field
from os import PathLike
from collections.abc import Sequence, Collection
from typing import List, Union

from mne import concatenate_raws, Epochs  # type: ignore
from mne.io.base import BaseRaw

from metapipe.interfaces import Processor, FileProcessor, Reader, Writer


MneContainer = Union[BaseRaw, Epochs]


@dataclass
class BandPassFilter(Processor):
    config: dict = field(default_factory=lambda: dict(l_freq=1, h_freq=100))

    def run(self, raw: MneContainer) -> MneContainer:
        return raw.copy().filter(**self.config)


class ConcatRaws(Processor):
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
class Resample(Processor):
    config: dict = field(default_factory=dict)

    def run(self, raw: MneContainer) -> MneContainer:
        return raw.copy().resample(**self.config)


@dataclass
class RawProcessorsChain(FileProcessor):
    """
    Read multiple raw objects, process them into one raw object and write

    """

    in_paths: Collection[PathLike]
    out_path: PathLike
    reader: Reader
    processors: Sequence[Processor]
    writer: Writer

    def _read_input(self) -> List:
        return [self.reader.read(p) for p in self.in_paths]

    def _write_output(self, result: BaseRaw) -> None:
        self.writer.write(result, self.out_path)

    def _process(self, in_objs: Sequence[BaseRaw]) -> BaseRaw:
        return self._run_processors(in_objs)

    def _run_processors(self, in_objs: Sequence[BaseRaw]) -> BaseRaw:
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
