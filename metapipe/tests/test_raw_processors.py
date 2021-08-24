from pytest import fixture
from dataclasses import dataclass, field

import mne
from mne.io import read_raw_fif
import numpy as np
from numpy.testing import assert_allclose

from metapipe.raw_processors import (
    BandPassFilter,
    ConcatRaws,
    Resample,
    RawFifReader,
    MneWriter,
    RawProcessorsChain
)
from metapipe.interfaces import RawReader, RawWriter, RawProcessor


@fixture
def simple_raw_factory():
    def wrapped(T_seconds, sfreq, n_channels, ch_type="eeg"):
        n_times = int(T_seconds * sfreq)

        data = np.random.rand(n_channels, n_times)
        info = mne.create_info(n_channels, ch_types=ch_type, sfreq=sfreq)

        return mne.io.RawArray(data, info)

    return wrapped


@fixture
def saved_fif_fpath_and_object(simple_raw_factory, tmp_raw_savepath):
    raw = simple_raw_factory(4, 300, 32)
    raw.save(tmp_raw_savepath)
    return tmp_raw_savepath, raw


@fixture
def tmp_raw_savepath(tmp_path):
    dest_path = tmp_path / "raw.fif"
    yield dest_path
    dest_path.unlink()


def test_band_pass_filter_filters_data(simple_raw_factory):
    raw = simple_raw_factory(4, 300, 32)
    filt = BandPassFilter()
    lf, hf = 1, 50
    filt.config["l_freq"] = lf
    filt.config["h_freq"] = hf
    raw_filt = filt.run(raw)
    assert raw_filt.info["highpass"] == lf
    assert raw_filt.info["lowpass"] == hf


def test_concat_with_same_channels(simple_raw_factory):
    raw = simple_raw_factory(1, 300, 33)
    cat = ConcatRaws()
    res = cat.run(raw, raw)
    assert res.n_times == raw.n_times * 2
    assert len(res.ch_names) == len(raw.ch_names)


def test_concat_single_object(simple_raw_factory):
    raw = simple_raw_factory(1, 300, 33)
    cat = ConcatRaws()
    res = cat.run(raw)
    assert_allclose(res.get_data(), raw.get_data())


def test_cat_with_different_channels_intersects_channels(simple_raw_factory):
    raw1 = simple_raw_factory(1, 300, 33)
    raw2 = simple_raw_factory(1, 300, 43)
    cat = ConcatRaws()
    res = cat.run(raw1, raw2)
    assert res.n_times == raw1.n_times + raw2.n_times
    assert len(res.ch_names) == len(raw1.ch_names)
    assert all(
        [
            ch_res == ch_raw1
            for ch_res, ch_raw1 in zip(res.ch_names, raw1.ch_names)
        ]
    )


def test_resample(simple_raw_factory):
    raw = simple_raw_factory(1, 300, 20)
    resamp = Resample()
    resamp.config["sfreq"] = 150
    result = resamp.run(raw)
    assert result.info["sfreq"] == 150


def test_fif_reader_reads_same_data(saved_fif_fpath_and_object):
    reader = RawFifReader()
    loaded_raw = reader.read(saved_fif_fpath_and_object[0])
    saved_raw = saved_fif_fpath_and_object[1]
    assert_allclose(loaded_raw.get_data(), saved_raw.get_data())


def test_mne_writer_data_unchanged(simple_raw_factory, tmp_raw_savepath):
    raw = simple_raw_factory(1, 300, 32)
    writer = MneWriter()
    writer.write(raw, tmp_raw_savepath)
    loaded_raw = read_raw_fif(tmp_raw_savepath)
    assert_allclose(raw.get_data(), loaded_raw.get_data())


@fixture
def mock_reader():
    @dataclass
    class MockRawReader(RawReader):
        config: dict = field(default_factory=dict)

        def read(self, path):
            return read_raw_fif(path, preload=True)

    return MockRawReader(config={})


@fixture
def mock_writer():
    @dataclass
    class MockWriter(RawWriter):
        config: dict = field(default_factory=dict)

        def write(self, raw, path):
            raw.save(path)

    return MockWriter(config={})


@fixture
def mock_processor():
    class MockProcessor(RawProcessor):
        """Append somethng to raw.info['description']"""

        def run(self, raw):
            cp = raw.copy()
            if cp.info["description"]:
                cp.info["description"] += ", mock-processed"
            else:
                cp.info["description"] = "mock-processed"

            return cp

    return MockProcessor()


def test_raw_processors_chain(
    mock_reader,
    mock_writer,
    mock_processor,
    saved_fif_fpath_and_object,
):
    raw_path = saved_fif_fpath_and_object[0]
    savepath = raw_path.parent / ("mock_processed_" + raw_path.name)
    chain = RawProcessorsChain(
        [raw_path],
        savepath,
        mock_reader,
        [mock_processor, mock_processor],
        mock_writer,
    )
    chain.run()
    raw_loaded = read_raw_fif(savepath)
    assert raw_loaded.info['description'] == "mock-processed, mock-processed"
