from pytest import fixture

import mne
from mne.channels import make_standard_montage
import numpy as np
from numpy.testing import assert_allclose

from metapipe.inmemo_processors import BandPassFilter, ConcatRaws, Resample


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
    dest_path.unlink()


def test_band_pass_filter_filters_data(simple_raw_factory):
    raw = simple_raw_factory(4, 300)
    filt = BandPassFilter()
    filt.config["l_freq"], filt.config["h_freq"] = lf, hf = 1, 50
    raw_filt = filt.run(raw)
    assert raw_filt.info["highpass"] == lf
    assert raw_filt.info["lowpass"] == hf


def test_concat_with_same_channels(simple_raw_factory):
    raw = simple_raw_factory(1, 300)
    cat = ConcatRaws()
    res = cat.run(raw, raw)
    assert res.n_times == raw.n_times * 2
    assert len(res.ch_names) == len(raw.ch_names)


def test_concat_single_object(simple_raw_factory):
    raw = simple_raw_factory(1, 300)
    cat = ConcatRaws()
    res = cat.run(raw)
    assert_allclose(res.get_data(), raw.get_data())


def test_cat_with_different_channels_intersects_channels(simple_raw_factory):
    raw1 = simple_raw_factory(1, 300, "biosemi32")
    raw2 = simple_raw_factory(1, 300, "biosemi16")
    cat = ConcatRaws()
    res = cat.run(raw1, raw2)
    assert res.n_times == raw1.n_times + raw2.n_times
    assert len(res.ch_names) == len(raw2.ch_names)
    assert set(res.ch_names) == set(raw2.ch_names)


def test_resample(simple_raw_factory):
    raw = simple_raw_factory(1, 300)
    resamp = Resample()
    resamp.config["sfreq"] = 150
    result = resamp.run(raw)
    assert result.info["sfreq"] == 150
