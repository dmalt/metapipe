from dataclasses import dataclass, field
from collections.abc import Collection

from mne import concatenate_raws  # type: ignore
from mne.io.base import BaseRaw  # type: ignore

from metapipe.abc import InMemoProcessor, MneContainer


@dataclass
class BandPassFilter(InMemoProcessor):
    config: dict = field(default_factory=lambda: dict(l_freq=1, h_freq=100))

    def run(self, raw: MneContainer) -> MneContainer:
        return raw.copy().filter(**self.config)


class ConcatRaws(InMemoProcessor):
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
class Resample(InMemoProcessor):
    config: dict = field(default_factory=dict)

    def run(self, raw: MneContainer) -> MneContainer:
        return raw.copy().resample(**self.config)
