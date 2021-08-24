from dataclasses import dataclass, field
from pytest import fixture

from mne.io import read_raw_fif

from metapipe.file_processors import ProcessorsChain
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


def test_processors_chain(
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
