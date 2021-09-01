import os.path as op
from dataclasses import dataclass, field
from os import PathLike, makedirs
from typing import Any, List, Sequence

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
    >>> builder = ProcessorsChain.Builder(rd, [flt], wrt)
    >>> filt = builder.with_deps(["in.fif"]).with_targets("out.fif").build()
    >>> print(filt.processors)
    [BandPassFilter(config={'l_freq': 1, 'h_freq': 100})]
    >>> # filt.run() # make sure "in.fif" exists

    Chain filtering and resampling

    >>> from metapipe.io import RawFifReader, MneWriter
    >>> from metapipe.inmemo_processors import BandPassFilter, Resample
    >>> rd, wrt = RawFifReader(), MneWriter()
    >>> flt = BandPassFilter(config = {"l_freq": 1, "h_freq": 100})
    >>> rsmp = Resample()
    >>> builder = ProcessorsChain.Builder(rd, [flt, rsmp], wrt)
    >>> chain = builder.with_deps(["in.fif"]).with_targets("out.fif").build()
    >>> print(chain.processors)
    [BandPassFilter(config={'l_freq': 1, 'h_freq': 100}), Resample(config={})]
    >>> # chain.run() # make sure in.fif exists

    """

    @dataclass
    class Builder(abc.BaseBuilder):
        reader: abc.Reader
        processors: Sequence[abc.InMemoProcessor]
        writer: abc.Writer

        def with_deps(self, in_paths: Sequence[PathLike]):  # type: ignore
            self._deps["in_paths"] = in_paths
            return self

        def with_targets(self, out_path: PathLike):  # type: ignore
            self._targets["out_path"] = out_path
            return self

        def build(self):
            self.check_ready()
            return ProcessorsChain(
                self._deps,
                self._targets,
                self.reader,
                self.processors,
                self.writer,
            )

        def check_ready(self):
            super().check_ready()
            if not self.processors:
                raise abc.BuilderNotReadyError(
                    "Must pass at least one processor (got none)"
                )

    reader: abc.Reader
    processors: Sequence[abc.InMemoProcessor]
    writer: abc.Writer

    def _read_input(self) -> List[Any]:
        return [self.reader.read(p) for p in self._deps["in_paths"]]

    def _process(self, data: Sequence[abc.MneContainer]) -> abc.MneContainer:
        # address the first processor separately since it's the only one
        # which possibly maps many to one, i.e. ConcatRaws; others - one to one
        intermediate = self.processors[0].run(*data)
        for node in self.processors[1:]:
            intermediate = node.run(intermediate)
        return intermediate

    def _write_output(self, result: abc.MneContainer) -> None:
        self.writer.write(result, self._targets["out_path"])


@dataclass
class IcaComputer(abc.ConfigurableFileProcessor):
    """
    Compute ICA solution on a raw file, possibly pre-filtering data

    Parameters
    ----------
    reader : format-specific class responsible for reading data from filesystem
    config : configuration

    """

    @dataclass
    class Builder(abc.BaseBuilder):
        reader: abc.Reader
        config: dict = field(
            default_factory=lambda: {
                "ICA": dict(n_components=0.99, random_state=42, max_iter=1000),
                "fit": dict(
                    decim=None, reject_by_annotation=True, picks="data"
                ),
                "filt": None,
            }
        )

        def with_deps(self, mne_container: PathLike) -> "IcaComputer.Builder":  # type: ignore # noqa
            self._deps["mne_container"] = mne_container
            return self

        def with_targets(self, ica: PathLike) -> "IcaComputer.Builder":  # type: ignore # noqa
            self._targets["ica"] = ica
            return self

        def build(self):
            self.check_ready()
            return IcaComputer(
                self._deps, self._targets, self.config, self.reader
            )

    reader: abc.Reader

    def _read_input(self) -> abc.MneContainer:
        return self.reader.read(self._deps["mne_container"])

    def _process(self, x: abc.MneContainer) -> ICA:
        ica = ICA(**self.config["ICA"])
        if self.config["filt"] is not None:
            x.filter(**self.config["filt"])
        ica.fit(x, **self.config["fit"])
        return ica

    def _write_output(self, ica: ICA) -> None:
        makedirs(op.dirname(self._targets["ica"]), exist_ok=True)
        ica.save(self._targets["ica"])


@dataclass
class IcaReportMaker(abc.FileProcessor):
    """
    Notes
    -----
    Works only for data with set montage. Montage can be set for example with
    raw.set_montage function

    """

    @dataclass
    class Builder(abc.BaseBuilder):
        reader: abc.Reader

        def with_deps(self, data: PathLike, ica: PathLike):  # type: ignore # noqa
            self._deps["data"] = data
            self._deps["ica"] = ica
            return self

        def with_targets(self, report: PathLike):  # type: ignore
            self._targets["report"] = report
            return self

        def build(self):
            self.check_ready()
            return IcaReportMaker(self._deps, self._targets, self.reader)

    reader: abc.Reader

    def _read_input(self):
        data = self.reader.read(self._deps["data"])
        ica = read_ica(self._deps["ica"])
        return data, ica

    def _process(self, in_objs):
        data, ica = in_objs
        report = Report(verbose=False)
        topos = ica.plot_components(picks=range(ica.n_components_), show=False)
        report.add_figs_to_section(topos, section="ICA", captions="Timeseries")
        return report

    def _write_output(self, report):
        report.save(
            self._targets["report"], overwrite=True, open_browser=False
        )


def main():
    import doctest  # pragma: no cover

    doctest.testmod()  # pragma: no cover


if __name__ == "__main__":
    main()  # pragma: no cover
