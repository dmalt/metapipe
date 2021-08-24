from mne.io import read_raw_fif
from numpy.testing import assert_allclose

from metapipe.io import RawFifReader, MneWriter
from metapipe.tests.test_raw_processors import (
    saved_fif_fpath_and_object,
    simple_raw_factory,
    tmp_raw_savepath,
)


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
