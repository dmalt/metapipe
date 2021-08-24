from pytest import fixture
from dataclasses import dataclass
from os import PathLike

from metapipe.interfaces import FileProcessor


@fixture
def tmp_text_fpath_and_str(tmp_path):
    string = "test\n"
    savepath = tmp_path / "test.txt"
    with open(savepath, "w") as f:
        f.write(string)
    return savepath, string


@fixture
def mock_concrete_file_io_node():
    @dataclass
    class ConcreteFileIoNode(FileProcessor):
        mock_file_in: PathLike
        mock_file_out: PathLike

        def _read_input(self):
            with open(self.mock_file_in, "r") as f:
                return [f.read()]

        def _process(self, in_objs):
            return in_objs[0] + ", mock-processed"

        def _write_output(self, result):
            with open(self.mock_file_out, "w") as f:
                f.write(result)

    return ConcreteFileIoNode


def test_file_io_node_reads_processes_and_runs(
    mock_concrete_file_io_node, tmp_text_fpath_and_str
):
    in_path, in_string = tmp_text_fpath_and_str
    out_path = in_path.parent / ("mock_processed_" + in_path.name)
    concrete_file_io_node = mock_concrete_file_io_node(in_path, out_path)
    concrete_file_io_node.run()
    with open(out_path, "r") as f:
        assert f.read() == in_string + ", mock-processed"
