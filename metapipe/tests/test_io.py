from pytest import fixture, mark  # type: ignore

from mne import Report  # type: ignore
from mne.io import read_raw_fif  # type: ignore
from mne.preprocessing import ICA  # type: ignore
from numpy.testing import assert_allclose  # type: ignore
from sklearn.exceptions import ConvergenceWarning  # type: ignore

from metapipe.io import (
    RawFifReader,
    MneWriter,
    IcaReader,
    IcaWriter,
    ReportWriter,
    RawAnnotator,
)
from metapipe.tests.test_processors import (  # type: ignore  # noqa
    saved_fif_fpath_and_object,  # noqa
    simple_raw_factory,  # noqa
    tmp_raw_savepath,  # noqa
    ica,  # noqa
)  # noqa


def test_fif_reader_reads_same_data(saved_fif_fpath_and_object):  # noqa
    reader = RawFifReader(saved_fif_fpath_and_object[0])
    loaded = reader.run()
    saved_raw = saved_fif_fpath_and_object[1]
    assert_allclose(loaded.raw.get_data(), saved_raw.get_data())


def test_mne_writer_data_unchanged(simple_raw_factory, tmp_raw_savepath):  # noqa
    raw = simple_raw_factory(1, 300)
    writer = MneWriter(tmp_raw_savepath)
    writer.run(raw)
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
@mark.filterwarnings("ignore", category=ConvergenceWarning)
def test_ica_reader_returns_ICA_obj(ica_path):
    node = IcaReader(ica_path)
    result = node.run()
    assert isinstance(result.ica, ICA)


@mark.filterwarnings("ignore", category=ConvergenceWarning)
def test_ica_writer(ica, tmp_path):  # noqa
    savepath = tmp_path / "writer_test_ica.fif"
    node = IcaWriter(savepath)
    node.run(ica)
    assert savepath.exists()


@fixture
def report():
    return Report(verbose=False)


@mark.slow
def test_ica_report_writer(report, tmp_path):
    savepath = tmp_path / "test_ica_report.html"
    node = ReportWriter(savepath)
    node.run(report)
    assert savepath.exists()
