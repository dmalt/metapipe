import os.path as op
from dataclasses import asdict, dataclass
from os import PathLike
from typing import Optional, Union

import mne  # type: ignore

from metapipe.abc import MneContainer, Processor


@dataclass
class Filter:
    """
    FIR filter class for raw data

    Parameters
    ----------
    l_freq : float | None
        Lower band-pass filter edge; if None, lowpass the data
    h_freq : float | None
        Higher band-pass filter edge; if None, highpass the data

    Notes
    -----
    One of l_freq, h_freq must be set

    See also
    --------
    mne.io.BaseRaw.filter()

    """

    l_freq: Optional[float]
    h_freq: Optional[float]

    def run(self, x: MneContainer) -> MneContainer:
        """
        Run filter

        Parameters
        ----------
        x : mne.io.BaseRaw | mne.Epochs

        Returns
        -------
        mne.io.BaseRaw | mne.Epochs
            Filtered data

        Warnings
        --------
        Filter is also applied to the passed data

        See also
        --------
        mne.io.BaseRaw.filter :
            BaseRaw method used under the hood to filter data

        """

        return x.filter(l_freq=self.l_freq, h_freq=self.h_freq)


@dataclass
class Resampler:
    """
    Raw data or epochs resampler

    Parameters
    ----------
    sfreq : float
        Resample to this frequency

    See also
    --------
    mne.io.BaseRaw.resample
        BaseRaw method used under the hood to resample data

    """

    sfreq: float

    def run(self, x: MneContainer) -> MneContainer:
        """
        Run resampler

        Parameters
        ----------
        x : mne.io.BaseRaw | mne.Epochs

        Returns
        -------
        mne.io.BaseRaw | mne.Epochs
            Resampled data
        """
        return x.resample(self.sfreq)


@dataclass
class IcaComputer:
    """
    Compute ICA solution on a raw file

    Parameters
    ----------
    n_components : int | float | None, default=0.99
        Number of components to use by actual number (int) or variance
        explained (float); None is equivalent to n_components = 0.9999999
    random_state: int | None, default=42
        If None, ICA solution is random; fix this number for reproducibility
    max_iter: int | None, default=1000
        Maximum number of iterations for optimization
    decim : int | None, default=None
        Decimation factor; set when computation is too slow or doesn't fit
        into memory
    picks : str | list | slice | None, default="data"
        Which channels to use for ICA; "data" picks only data channels
        (no ecg, eog, etc.), "all" or None picks all channels. More flexible
        setup is available, see docs for mne.preprocessing.ICA.fit()


    See also
    --------
    mne.preprocessing.ICA
    mne.preprocessing.ICA.fit

    """

    n_components: Optional[Union[float, int]] = 0.99
    random_state: int = 42
    max_iter: int = 1000
    decim: Optional[int] = None
    reject_by_annotation: bool = True
    picks: Optional[Union[str, list, slice]] = "data"

    def run(self, x: MneContainer) -> mne.preprocessing.ICA:
        """
        Fit ICA to data

        Parameters
        ----------
        x: mne.io.BaseRaw | mne.Epochs
            Data to fit ICA on

        Returns
        -------
        mne.preprocessing.ICA
            Fitted ICA solution

        """
        ica = mne.preprocessing.ICA(
            n_components=self.n_components,
            max_iter=self.max_iter,
            random_state=self.random_state,
        )
        ica.fit(
            x,
            decim=self.decim,
            reject_by_annotation=self.reject_by_annotation,
            picks=self.picks,
        )
        return ica


@dataclass
class IcaReportMaker(Processor):
    """
    HTML report creator for ICA solution

    Parameters
    ----------
    section: str, default="ICA"
        ICA section name as it would appear in the report
    captions: str



    Notes
    -----
    Works only for data with set montage. This is not the case for some EEG
    data formats, such as Brainvision.  Montage can be set for example with
    raw.set_montage() function

    See also
    --------
    mne.Report :
        MNE-Python class for generating reports
    mne.preprocessing.ICA.plot_components :
        Function used under the hood to plot ICA topographies

    """

    section: str = "ICA"
    captions: str = "Topographies"

    def run(self, ica: mne.preprocessing.ICA) -> mne.Report:
        """ """
        report = mne.Report(verbose=False)
        topos = ica.plot_components(picks=range(ica.n_components_), show=False)
        report.add_figs_to_section(topos, **asdict(self))
        return report


def set_annotations(annots: PathLike, raw: mne.io.BaseRaw) -> mne.io.BaseRaw:
    if op.exists(annots):
        annot = mne.read_annotations(annots)
        raw.set_annotations(annot)
    return raw


def concatenate_raws(*raws: mne.io.BaseRaw) -> mne.io.BaseRaw:
    """Concatenate common channels from raw objects"""
    if len(raws) == 1:
        return raws[0]
    common_ch_names = set.intersection(*[set(r.ch_names) for r in raws])
    raws_sel = [raw.pick_channels(list(common_ch_names)) for raw in raws]
    # assert False
    return mne.concatenate_raws(raws_sel)
