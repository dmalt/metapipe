from dataclasses import dataclass, field
from os import PathLike
from typing import NamedTuple

from mne import Report, Annotations  # type: ignore
from mne.io import Raw, read_raw_fif, read_raw_brainvision, BaseRaw  # type: ignore # noqa
from mne.preprocessing import ICA, read_ica  # type: ignore

from metapipe.abc import Reader, Writer, MneContainer


@dataclass
class RawFifReader(Reader):
    class OutSpec(NamedTuple):
        raw: Raw

    path: PathLike
    config: dict = field(default_factory=lambda: dict(preload=True))

    def run(self) -> OutSpec:
        return self.OutSpec(read_raw_fif(self.path, **self.config))


@dataclass
class BrainvisionReader(Reader):
    class OutSpec(NamedTuple):
        raw: Raw

    path: PathLike
    config: dict = field(default_factory=lambda: dict(preload=True))

    def run(self) -> OutSpec:
        return self.OutSpec(read_raw_brainvision(self.path, **self.config))  # pragma: no cover # noqa


@dataclass
class MneWriter(Writer):
    path: PathLike
    config: dict = field(default_factory=dict)

    def run(self, raw: MneContainer) -> None:
        raw.save(self.path, **self.config)


class MneBidsWriter(Writer):
    """Write raw file together with BIDS metainfo"""

    pass


@dataclass
class IcaReader(Reader):
    class OutSpec(NamedTuple):
        ica: ICA

    path: PathLike
    config: dict = field(default_factory=lambda: {"verbose": None})

    def run(self) -> OutSpec:
        return self.OutSpec(read_ica(self.path, **self.config))


@dataclass
class IcaWriter(Writer):
    path: PathLike
    config: dict = field(default_factory=lambda: {"verbose": None})

    def run(self, ica: ICA) -> None:
        ica.save(self.path, **self.config)


@dataclass
class ReportWriter(Writer):
    path: PathLike
    config: dict = field(
        default_factory=lambda: {"overwrite": True, "open_browser": False}
    )

    def run(self, report: Report) -> None:
        report.save(self.path, **self.config)


@dataclass
class RawAnnotator(Writer):
    path: PathLike
    config: dict = field(
        default_factory=lambda: dict(
            plot=dict(block=True, lowpass=100, n_channels=102),
            pick_types=None,
            save=dict(overwrite=True),
        )
    )

    def run(self, raw_check: BaseRaw) -> Annotations:
        if self.config["pick_types"] is not None:
            raw_check.pick_types(**self.config["pick_types"])
        raw_check.plot(**self.config["plot"])
        raw_check.annotations.save(self.path, **self.config["save"])
