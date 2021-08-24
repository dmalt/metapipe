from dataclasses import dataclass, field
from pytest import fixture, raises

from mne.io import read_raw_fif

from metapipe.file_processors import ProcessorsChain, ComputeIca, MakeIcaReport
from metapipe.abc import Reader, Writer, InMemoProcessor
from metapipe.tests.test_inmemo_processors import (  # noqa
    saved_fif_fpath_and_object,  # noqa
    simple_raw_factory,  # noqa
    tmp_raw_savepath,  # noqa
)  # noqa


@fixture
def mock_reader():
    @dataclass
    class MockRawReader(Reader):
        config: dict = field(default_factory=dict)

        def read(self, path):
            return read_raw_fif(path, preload=True)

    return MockRawReader(config={})


@fixture
def mock_writer():
    @dataclass
    class MockWriter(Writer):
        config: dict = field(default_factory=dict)

        def write(self, raw, path):
            raw.save(path)

    return MockWriter(config={})


@fixture
def mock_processor():
    """Processor which adds 'mock-processed' substring to description"""

    class MockProcessor(InMemoProcessor):
        """Append somethng to raw.info['description']"""

        def run(self, raw):
            cp = raw.copy()
            if cp.info["description"]:
                cp.info["description"] += ", mock-processed"
            else:
                cp.info["description"] = "mock-processed"

            return cp

    return MockProcessor()


def test_processors_chain_of_mock_processors_adds_to_description(
    mock_reader,
    mock_writer,
    mock_processor,
    saved_fif_fpath_and_object,  # noqa
):
    raw_path = saved_fif_fpath_and_object[0]
    savepath = raw_path.parent / ("mock_processed_" + raw_path.name)
    chain = ProcessorsChain(
        [raw_path],
        savepath,
        mock_reader,
        [mock_processor, mock_processor],
        mock_writer,
    )
    chain.run()
    raw_loaded = read_raw_fif(savepath)
    assert raw_loaded.info["description"] == "mock-processed, mock-processed"


def test_processors_chain_raises_exception_when_no_processors_supplied(
    mock_reader, mock_writer
):
    with raises(ValueError):
        ProcessorsChain(["in.fif"], "out.fif", mock_reader, [], mock_writer)


def test_compute_ica_saves_file(mock_reader, saved_fif_fpath_and_object):  # noqa
    raw_path = saved_fif_fpath_and_object[0]
    savepath = raw_path.parent / (
        "mock_processed_" + raw_path.stem + "_ica.fif"
    )
    ica_node = ComputeIca(raw_path, mock_reader, savepath)
    ica_node.run()
    assert savepath.exists()
    savepath.unlink()


@fixture
def raw_and_ica_sol(saved_fif_fpath_and_object, mock_reader):  # noqa
    raw_path = saved_fif_fpath_and_object[0]
    ica_path = raw_path.parent / (
        "mock_processed_" + raw_path.stem + "_ica.fif"
    )
    ica_node = ComputeIca(raw_path, mock_reader, ica_path)
    ica_node.run()
    yield raw_path, ica_path
    ica_path.unlink()


def test_make_ica_report_produces_html_file(mock_reader, raw_and_ica_sol):
    raw_path, ica_path = raw_and_ica_sol
    report_path = ica_path.parent / (ica_path.stem + "_report.html")
    report_node = MakeIcaReport(raw_path, mock_reader, ica_path, report_path)
    report_node.run()
    assert report_path.exists()
    report_path.unlink()
