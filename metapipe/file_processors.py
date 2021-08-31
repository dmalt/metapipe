from dataclasses import dataclass, field
from os import PathLike, makedirs
import os.path as op
from typing import List, Sequence, NamedTuple

from mne import Report  # type: ignore
from mne.preprocessing import ICA, read_ica  # type: ignore

from metapipe import abc


@dataclass
class ProcessorsChain(abc.FileProcessor):
    """
    Read multiple raw objects, process them into one raw object and write

    Examples
    --------

    Create raw filtering chain

    >>> from metapipe.io import RawFifReader, MneWriter
    >>> from metapipe.inmemo_processors import BandPassFilter
    >>> rd, wrt = RawFifReader(), MneWriter()
    >>> flt = BandPassFilter(config = {"l_freq": 1, "h_freq": 100})
    >>> filt_chain = ProcessorsChain(rd, [flt], wrt)
    >>> print(filt_chain.processors)
    [BandPassFilter(config={'l_freq': 1, 'h_freq': 100})]

    Chain filtering and resampling

    >>> from metapipe.io import RawFifReader, MneWriter
    >>> from metapipe.inmemo_processors import BandPassFilter, Resample
    >>> rd, wrt = RawFifReader(), MneWriter()
    >>> flt = BandPassFilter(config = {"l_freq": 1, "h_freq": 100})
    >>> rsmp = Resample()
    >>> filt_chain = ProcessorsChain(rd, [flt, rsmp], wrt)
    >>> print(filt_chain.processors)
    [BandPassFilter(config={'l_freq': 1, 'h_freq': 100}), Resample(config={})]

    """

    class InPaths(NamedTuple):
        in_paths: Sequence[PathLike]

    class OutPaths(NamedTuple):
        out_path: PathLike

    reader: abc.Reader
    processors: Sequence[abc.InMemoProcessor]
    writer: abc.Writer

    def __post_init__(self) -> None:
        if not self.processors:
            raise ValueError("Must pass at least one processor (got none)")

    def _read_input(self, deps: "InPaths") -> List:
        return [self.reader.read(p) for p in deps.in_paths]

    def _process(self, data: Sequence[abc.MneContainer]) -> abc.MneContainer:
        # address the first processor separately since it's the only one
        # which possibly maps many to one, i.e. ConcatRaws; others - one to one
        intermediate = self.processors[0].run(*data)
        for node in self.processors[1:]:
            intermediate = node.run(intermediate)
        return intermediate

    def _write_output(
        self, result: abc.MneContainer, targets: "OutPaths"
    ) -> None:
        self.writer.write(result, targets.out_path)


@dataclass
class IcaComputer(abc.ConfigurableFileProcessor):
    """
    Compute ICA solution on a raw file, possibly pre-filtering data

    Parameters
    ----------
    reader : format-specific class responsible for reading data from filesystem
    config : configuration

    Examples
    --------

    """

    class InPaths(NamedTuple):
        mne_container: PathLike

    class OutPaths(NamedTuple):
        ica: PathLike

    reader: abc.Reader
    config: dict = field(
        default_factory=lambda: {
            "ICA": dict(n_components=0.99, random_state=42, max_iter=1000),
            "fit": dict(decim=None, reject_by_annotation=True, picks="data"),
            "filt": None,
        }
    )

    def _read_input(self, in_paths: "InPaths") -> abc.MneContainer:
        return self.reader.read(in_paths.mne_container)

    def _process(self, x: abc.MneContainer) -> ICA:
        ica = ICA(**self.config["ICA"])
        if self.config["filt"] is not None:
            x.filter(**self.config["filt"])
        ica.fit(x, **self.config["fit"])
        return ica

    def _write_output(self, ica: ICA, out_paths: "OutPaths") -> None:
        makedirs(op.dirname(out_paths.ica), exist_ok=True)
        ica.save(out_paths.ica)


@dataclass
class IcaReportMaker(abc.FileProcessor):
    """
    Notes
    -----
    Works only for data with set montage. Montage can be set for example with
    raw.set_montage function

    """
    class InPaths(NamedTuple):
        data: PathLike
        ica: PathLike

    class OutPaths(NamedTuple):
        report: PathLike

    reader: abc.Reader

    def _read_input(self, deps: InPaths):
        data = self.reader.read(deps.data)
        ica = read_ica(deps.ica)
        return data, ica

    def _process(self, in_objs):
        data, ica = in_objs
        report = Report(verbose=False)
        topos = ica.plot_components(picks=range(ica.n_components_), show=False)
        report.add_figs_to_section(topos, section="ICA", captions="Timeseries")
        return report

    def _write_output(self, report, targets: "OutPaths"):
        report.save(targets.report, overwrite=True, open_browser=False)


def main():
    import doctest

    doctest.testmod()


if __name__ == "__main__":
    main()
