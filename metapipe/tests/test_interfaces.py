from dataclasses import dataclass
from os import PathLike

from pytest import fixture, raises

from metapipe.abc import FileProcessor, BuilderNotReadyError, BaseBuilder


@fixture
def text_dep(tmp_path):
    string = "test\n"
    savepath = tmp_path / "test.txt"
    with open(savepath, "w") as f:
        f.write(string)
    return savepath, string


@fixture
def MockFileProcessor():
    @dataclass
    class ConcreteFileProcessor(FileProcessor):
        @dataclass
        class Builder(BaseBuilder):
            def with_deps(self, mock_file_in: PathLike):
                self._deps["mock_file_in"] = mock_file_in
                return self

            def with_targets(self, mock_file_out: PathLike):
                self._targets["mock_file_out"] = mock_file_out
                return self

            def build(self):
                self.check_ready()
                return ConcreteFileProcessor(self._deps, self._targets)

        def _read_input(self):
            with open(self._deps["mock_file_in"], "r") as f:
                return [f.read()]

        def _process(self, in_objs):
            return in_objs[0] + ", mock-processed"

        def _write_output(self, result):
            with open(self._targets["mock_file_out"], "w") as f:
                f.write(result)

    return ConcreteFileProcessor


def test_file_processor_affects_target_file(MockFileProcessor, text_dep):
    in_path, in_string = text_dep
    out_path = in_path.parent / ("mock_processed_" + in_path.name)
    builder = MockFileProcessor.Builder()
    node = builder.with_deps(in_path).with_targets(out_path).build()
    node.run()
    with open(out_path, "r") as f:
        assert f.read() == in_string + ", mock-processed"


def test_file_processor_provides_deps_readonly_property(MockFileProcessor):
    builder = MockFileProcessor.Builder()
    node = builder.with_deps("in.fif").with_targets("out.fif").build()
    assert node.deps == ["in.fif"]
    with raises(AttributeError):
        node.deps = ["a.fif"]


def test_file_processor_provides_targets_readonly_property(MockFileProcessor):
    builder = MockFileProcessor.Builder()
    node = builder.with_deps("in.fif").with_targets("out.fif").build()
    assert node.targets == ["out.fif"]
    with raises(AttributeError):
        node.targets = ["a.fif"]


def test_builder_deps_set_after_with_deps(MockFileProcessor):
    builder = MockFileProcessor.Builder()
    builder.with_deps("in.fif")
    assert builder.deps == ["in.fif"]


def test_builder_targets_set_after_with_targets(MockFileProcessor):
    builder = MockFileProcessor.Builder()
    builder.with_targets("out.fif")
    assert builder.targets == ["out.fif"]


def test_builder_is_ready_after_setting_all_required_attrs(MockFileProcessor):
    builder = MockFileProcessor.Builder()
    builder.with_deps("in.fif").with_targets("out.fif")
    assert builder.is_ready()


def test_builder_raises_exception_when_not_ready(MockFileProcessor):
    builder = MockFileProcessor.Builder()
    with raises(BuilderNotReadyError):
        builder.build()
    with raises(BuilderNotReadyError):
        builder.with_deps("in.fif").build()


def test_builder_not_ready_without_deps(MockFileProcessor):
    builder = MockFileProcessor.Builder()
    assert not builder.is_ready()
    builder.with_targets("out.fif")
    assert not builder.is_ready()


def test_builder_not_ready_without_targets(MockFileProcessor):
    builder = MockFileProcessor.Builder()
    assert not builder.is_ready()
    builder.with_deps("in.fif")
    assert not builder.is_ready()
