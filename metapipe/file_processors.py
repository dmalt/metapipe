from dataclasses import dataclass, field
from os import PathLike
from typing import Collection, List, Sequence

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
    reader: abc.Reader
    processors: Sequence[abc.InMemoProcessor]
    writer: abc.Writer

    def __post_init__(self) -> None:
        if not self.processors:
            raise ValueError("Must pass at least one processor (got none)")

    def _read_input(self) -> List:
        return [self.reader.read(p) for p in self.in_paths]

    def _process(self, data: Sequence[abc.MneContainer]) -> abc.MneContainer:
        # address the first processor separately since it's the only one
        # which possibly maps many to one, i.e. ConcatRaws; others - one to one
        intermediate = self.processors[0].run(*data)
        for node in self.processors[1:]:
            intermediate = node.run(intermediate)
        return intermediate

    def _write_output(self, result: abc.MneContainer) -> None:
        self.writer.write(result, self.out_path)


@dataclass
class ComputeIca(abc.FileProcessor):
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
    reader: abc.Reader
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

    def _read_input(self) -> abc.MneContainer:
        return self.reader.read(self.in_path)

    def _process(self, data: abc.MneContainer) -> ICA:
        ica = ICA(**self.construct_config)
        ica.fit(data, **self.fit_config)
        return ica

    def _write_output(self, ica: ICA) -> None:
        ica.save(self.ica_sol_out_path)


@dataclass
class MakeIcaReport(abc.FileProcessor):
    """
    Notes
    -----
    Works only for data with set montage. Montage can be set for example with
    raw.set_montage function

    """
    in_data_path: PathLike
    reader: abc.Reader
    in_ica_sol_path: PathLike
    out_report_path: PathLike

    def _read_input(self):
        data = self.reader.read(self.in_data_path)
        ica = read_ica(self.in_ica_sol_path)
        return data, ica

    def _process(self, in_objs):
        data, ica = in_objs
        report = Report(verbose=False)
        topos = ica.plot_components(picks=range(ica.n_components_), show=False)
        report.add_figs_to_section(topos, section="ICA", captions="Timeseries")
        return report

    def _write_output(self, report):
        report.save(self.out_report_path, overwrite=True, open_browser=False)


def main():
    import doctest

    doctest.testmod()


if __name__ == "__main__":
    main()
