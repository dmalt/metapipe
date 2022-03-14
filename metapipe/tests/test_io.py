from mne import Report  # type: ignore
from mne.io import read_raw_fif  # type: ignore
from mne.preprocessing import ICA  # type: ignore
from numpy.testing import assert_allclose  # type: ignore
from pytest import fixture, mark  # type: ignore

from metapipe import io
from metapipe.tests.test_processors import ica  # type: ignore # noqa
from metapipe.tests.test_processors import saved_fif_fpath_and_object  # noqa
from metapipe.tests.test_processors import simple_raw_factory  # noqa
from metapipe.tests.test_processors import \
    tmp_raw_savepath  # type: ignore # noqa


def test_fif_reader_reads_same_data(saved_fif_fpath_and_object):  # noqa
    reader = io.RawFifReader()
    loaded = reader.run(saved_fif_fpath_and_object[0])
    saved_raw = saved_fif_fpath_and_object[1]
    assert_allclose(loaded.get_data(), saved_raw.get_data())


def test_mne_writer_data_unchanged(simple_raw_factory, tmp_raw_savepath):  # noqa
    raw = simple_raw_factory(1, 300)
    writer = io.MneWriter()
    writer.run(tmp_raw_savepath, raw)
    loaded_raw = read_raw_fif(tmp_raw_savepath)
    assert_allclose(raw.get_data(), loaded_raw.get_data())


@fixture
def ica_path(tmp_path, ica):  # noqa
    savepath = tmp_path / "test_ica.fif"
    ica.save(savepath)
    yield savepath
    if savepath.exists():
        savepath.unlink()


@mark.slow
def test_ica_reader_returns_ICA_obj(ica_path):
    node = io.IcaReader()
    ica_sol = node.run(ica_path)
    assert isinstance(ica_sol, ICA)


def test_ica_writer(ica, tmp_path):  # noqa
    savepath = tmp_path / "writer_test_ica.fif"
    node = io.IcaWriter()
    node.run(savepath, ica)
    assert savepath.exists()


@fixture
def report():
    return Report(verbose=False)


@mark.slow
def test_ica_report_writer(report, tmp_path):
    savepath = tmp_path / "test_ica_report.html"
    node = io.ReportWriter()
    node.run(savepath, report)
    assert savepath.exists()
