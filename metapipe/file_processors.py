from dataclasses import dataclass, field
from os import PathLike
from typing import Sequence, Collection, List

from mne.preprocessing import ICA  # type: ignore

from metapipe.abc import (
    FileProcessor,
    Reader,
    Writer,
    InMemoProcessor,
    MneContainer,
)


@dataclass
class ProcessorsChain(FileProcessor):
    """
    Read multiple raw objects, process them into one raw object and write

    Examples
    --------

    Create raw filtering chain

    >>> from metapipe.io import RawFifReader, MneWriter
    >>> from metapipe.inmemo_processors import BandPassFilter
    >>> rd, wrt = RawFifReader(), MneWriter()
    >>> flt = BandPassFilter(config = {"l_freq": 1, "h_freq": 100})
    >>> filt_chain = ProcessorsChain(["i.fif"], "o.fif", rd, [flt], wrt)
    >>> print(filt_chain.processors)
    [BandPassFilter(config={'l_freq': 1, 'h_freq': 100})]

    Chain filtering and resampling

    >>> from metapipe.io import RawFifReader, MneWriter
    >>> from metapipe.inmemo_processors import BandPassFilter, Resample
    >>> rd, wrt = RawFifReader(), MneWriter()
    >>> flt = BandPassFilter(config = {"l_freq": 1, "h_freq": 100})
    >>> rsmp = Resample()
    >>> filt_chain = ProcessorsChain(["i.fif"], "o.fif", rd, [flt, rsmp], wrt)
    >>> print(filt_chain.processors)
    [BandPassFilter(config={'l_freq': 1, 'h_freq': 100}), Resample(config={})]

    """

    in_paths: Collection[PathLike]
    out_path: PathLike
    reader: Reader
    processors: Sequence[InMemoProcessor]
    writer: Writer

    def _read_input(self) -> List:
        return [self.reader.read(p) for p in self.in_paths]

    def _write_output(self, result: MneContainer) -> None:
        self.writer.write(result, self.out_path)

    def _process(self, in_objs: Sequence[MneContainer]) -> MneContainer:
        return self._run_processors(in_objs)

    def _run_processors(self, in_objs: Sequence[MneContainer]) -> MneContainer:
        assert self.processors, "Must pass at least one processor"
        intermediate_raw = self.processors[0].run(*in_objs)
        for node in self.processors[1:]:
            intermediate_raw = node.run(intermediate_raw)
        return intermediate_raw


@dataclass
class ComputeIca(FileProcessor):
    """
    Compute ICA solution on a raw file

    Parameters
    ----------
    in_path : path to BaseRaw or Epohcs object
    reader : format-specific class responsible for reading data from filesystem
    ica_sol_out_path : path to save the ICA solution to
    construct_config : config options for mne.preprocessing.ICA constructior
    fit_config : configuration for ICA.fit()

    """

    in_path: PathLike
    reader: Reader
    ica_sol_out_path: PathLike
    construct_config: dict = field(
        default_factory=lambda: dict(
            n_components=0.99, random_state=42, max_iter=1000
        )
    )
    fit_config: dict = field(
        default_factory=lambda: dict(
            decim=None, reject_by_annotation=True, picks="data"
        )
    )

    def _read_input(self):
        return self.reader.read(self.in_path)

    def _process(self, raw):
        ica = ICA(**self.construct_config)
        ica.fit(raw, **self.fit_config)
        return ica

    def _write_output(self, ica):
        ica.save(self.ica_sol_out_path)


def main():
    import doctest

    doctest.testmod()


if __name__ == "__main__":
    main()
