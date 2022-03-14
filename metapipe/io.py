from dataclasses import dataclass
from os import PathLike
from typing import Optional

import mne  # type: ignore
from mne import Report  # type: ignore
from mne.io import (BaseRaw, Raw, read_raw_brainvision,  # type: ignore # noqa
                    read_raw_fif)

from metapipe.abc import MneContainer, Reader, Writer


@dataclass
class RawFifReader(Reader):
    preload: bool = True

    def run(self, path: PathLike) -> mne.io.Raw:
        return read_raw_fif(path, preload=self.preload)


@dataclass
class BrainvisionReader(Reader):
    preload: bool = True

    def run(self, path: PathLike) -> mne.io.Raw:
        return read_raw_brainvision(path, preload=self.preload)


class MneWriter(Writer):
    """Write mne container"""
    def run(self, savepath: PathLike, raw: MneContainer) -> None:
        raw.save(savepath)


class MneBidsWriter(Writer):
    """Write raw file together with BIDS metainfo"""

    pass


@dataclass
class IcaReader(Reader):
    """Read ICA solution"""
    verbose: Optional[str] = None

    def run(self, path: PathLike) -> mne.preprocessing.ICA:
        return mne.preprocessing.read_ica(path, verbose=self.verbose)


@dataclass
class IcaWriter(Writer):
    """Write ICA solution"""
    verbose: Optional[str] = None

    def run(self, savepath: PathLike, ica: mne.preprocessing.ICA) -> None:
        ica.save(savepath, verbose=self.verbose)


@dataclass
class ReportWriter(Writer):
    """Write mne report"""
    overwrite: bool = True
    open_browser: bool = False

    def run(self, savepath: PathLike, report: Report) -> None:
        report.save(
            savepath, overwrite=self.overwrite, open_browser=self.open_browser
        )


@dataclass
class RawAnnotator(Writer):
    """Visually annotate raw file and save annotations"""
    block: bool = True
    lowpass: float = 100
    n_channels: int = 102
    pick_types: Optional[str] = None
    overwrite: bool = True

    def run(self, savepath: PathLike, raw_check: BaseRaw) -> None:
        if self.pick_types is not None:
            raw_check.pick_types(self.pick_types)
        raw_check.plot(
            block=self.block, lowpass=self.lowpass, n_channels=self.n_channels
        )
        raw_check.annotations.save(savepath, overwrite=self.overwrite)
