from pytest import fixture, mark  # type: ignore

import mne  # type: ignore
from mne.channels import make_standard_montage  # type: ignore
from mne.preprocessing import ICA  # type: ignore
from mne import Annotations, read_annotations  # type: ignore
import numpy as np  # type: ignore
from numpy.testing import assert_allclose  # type: ignore

from metapipe.processors import (
    Filter,
    RawsCat,
    Resampler,
    IcaComputer,
    IcaReportMaker,
    AnnotSetter,
)


@fixture
def simple_raw_factory():
    def wrapped(T_seconds, sfreq, montage_type="biosemi32"):
        ch_type = "eeg"
        n_times = int(T_seconds * sfreq)
        montage = make_standard_montage(montage_type)
        ch_names = montage.ch_names
        n_channels = len(ch_names)

        data = np.random.rand(n_channels, n_times)
        info = mne.create_info(ch_names, ch_types=ch_type, sfreq=sfreq)
        raw = mne.io.RawArray(data, info)
        raw.set_montage(montage)

        return raw

    return wrapped


@fixture
def saved_fif_fpath_and_object(simple_raw_factory, tmp_raw_savepath):
    raw = simple_raw_factory(4, 300)
    raw.save(tmp_raw_savepath)
    return tmp_raw_savepath, raw


@fixture
def tmp_raw_savepath(tmp_path):
    dest_path = tmp_path / "raw.fif"
    yield dest_path
    if dest_path.exists():
        dest_path.unlink()


def test_band_pass_filter_filters_data(simple_raw_factory):
    raw = simple_raw_factory(4, 300)
    filt = Filter()
    filt.config["l_freq"], filt.config["h_freq"] = lf, hf = 1, 50
    raw_filt = filt.run(raw)
    assert raw_filt.mne_container.info["highpass"] == lf
    assert raw_filt.mne_container.info["lowpass"] == hf


def test_concat_with_same_channels(simple_raw_factory):
    raw = simple_raw_factory(1, 300)
    orig = raw.copy()
    cat = RawsCat()
    res = cat.run(raw, raw)
    assert res.cat_raws.n_times == orig.n_times * 2
    assert len(res.cat_raws.ch_names) == len(raw.ch_names)


def test_concat_single_object(simple_raw_factory):
    raw = simple_raw_factory(1, 300)
    cat = RawsCat()
    res = cat.run(raw)
    assert_allclose(res.cat_raws.get_data(), raw.get_data())


def test_cat_with_different_channels_intersects_channels(simple_raw_factory):
    raw1 = simple_raw_factory(1, 300, "biosemi32")
    raw2 = simple_raw_factory(1, 300, "biosemi16")
    cat = RawsCat()
    res = cat.run(raw1.copy(), raw2.copy())
    assert res.cat_raws.n_times == raw1.n_times + raw2.n_times
    assert len(res.cat_raws.ch_names) == len(raw2.ch_names)
    assert set(res.cat_raws.ch_names) == set(raw2.ch_names)


def test_resample(simple_raw_factory):
    raw = simple_raw_factory(1, 300)
    resamp = Resampler()
    resamp.config["sfreq"] = 150
    result = resamp.run(raw)
    assert result.mne_container.info["sfreq"] == 150


def test_ica_computer_fits_ica(simple_raw_factory):  # noqa
    raw = simple_raw_factory(4, 200)
    raw.filter(l_freq=1, h_freq=None)

    ica_computer = IcaComputer()
    ica_computer.config["ICA"]["max_iter"] = 100
    result = ica_computer.run(raw)
    assert hasattr(result.ica, "n_components_")


@fixture
def ica(simple_raw_factory):
    raw = simple_raw_factory(4, 300)
    raw.filter(l_freq=1, h_freq=None)
    ica = ICA(max_iter=100, method="picard")
    ica.fit(raw)
    return ica


@mark.slow
def test_ica_report_maker(ica):
    node = IcaReportMaker()
    result = node.run(ica)
    assert result.report.sections == [node.config["section"]]


@fixture
def annot_path(tmp_path):
    my_annot = Annotations(onset=[0.5],  # in seconds
                           duration=[0.2],  # in seconds, too
                           description=['test'])
    dest_path = tmp_path / "test_annot.fif"
    my_annot.save(dest_path)
    yield dest_path
    if dest_path.exists():
        dest_path.unlink()


def test_annot_setter(annot_path, simple_raw_factory):
    node = AnnotSetter(annot_path)
    raw = simple_raw_factory(1, 100)
    result = node.run(raw)
    annots = read_annotations(annot_path)
    assert result.raw.annotations == annots
