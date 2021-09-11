from os import PathLike
import os.path as op
from dataclasses import dataclass, field
from typing import NamedTuple, Sequence

from mne import concatenate_raws  # type: ignore
from mne.io.base import BaseRaw  # type: ignore
from mne.preprocessing import ICA  # type: ignore
from mne import Report, read_annotations  # type: ignore

from metapipe.abc import Processor, MneContainer


@dataclass
class Filter(Processor):
    class OutSpec(NamedTuple):
        mne_container: MneContainer

    config: dict = field(default_factory=lambda: dict(l_freq=1, h_freq=100))

    def run(self, mne_container: MneContainer) -> OutSpec:
        return self.OutSpec(mne_container.filter(**self.config))


class RawsCat(Processor):
    """Concatenate common channels from raw objects"""

    class OutSpec(NamedTuple):
        cat_raws: BaseRaw

    def run(self, *raws: Sequence[BaseRaw]) -> OutSpec:
        if len(raws) == 1:
            return self.OutSpec(raws[0])
        raws = self._intersect_chs(raws)
        return self.OutSpec(concatenate_raws(raws))

    def _intersect_chs(self, raws: Sequence[BaseRaw]):
        common_ch_names = set.intersection(*[set(r.ch_names) for r in raws])
        return [raw.pick_channels(list(common_ch_names)) for raw in raws]


@dataclass
class Resampler(Processor):
    class OutSpec(NamedTuple):
        mne_container: MneContainer

    config: dict = field(default_factory=dict)

    def run(self, mne_container: MneContainer) -> OutSpec:
        return self.OutSpec(mne_container.resample(**self.config))


@dataclass
class IcaComputer(Processor):
    """
    Compute ICA solution on a raw file, possibly pre-filtering data

    Parameters
    ----------
    reader : format-specific class responsible for reading data from filesystem
    config : configuration

    """

    class OutSpec(NamedTuple):
        ica: ICA

    config: dict = field(
        default_factory=lambda: {
            "ICA": dict(n_components=0.99, random_state=42, max_iter=1000),
            "fit": dict(decim=None, reject_by_annotation=True, picks="data"),
        }
    )

    def run(self, mne_container: MneContainer) -> OutSpec:
        ica = ICA(**self.config["ICA"])
        ica.fit(mne_container, **self.config["fit"])
        return self.OutSpec(ica)


@dataclass
class IcaReportMaker(Processor):
    """
    Notes
    -----
    Works only for data with set montage. Montage can be set for example with
    raw.set_montage function

    """

    class OutSpec(NamedTuple):
        report: Report

    config: dict = field(
        default_factory=lambda: dict(section="ICA", captions="Topographies")
    )

    def run(self, ica: ICA) -> Report:
        report = Report(verbose=False)
        topos = ica.plot_components(picks=range(ica.n_components_), show=False)
        report.add_figs_to_section(topos, **self.config)
        return self.OutSpec(report)


@dataclass
class AnnotSetter(Processor):
    class OutSpec(NamedTuple):
        raw: BaseRaw

    annot_path: PathLike
    config: dict = field(
        default_factory=lambda: dict(
            read_annotations=dict(),
            set_annotations=dict(),
        )
    )

    def run(self, raw: BaseRaw) -> OutSpec:
        if op.exists(self.annot_path):
            annot = read_annotations(
                self.annot_path, **self.config["read_annotations"]
            )
            raw.set_annotations(annot, **self.config["set_annotations"])
        return self.OutSpec(raw)
