from dataclasses import dataclass
from os import PathLike
from typing import NamedTuple
from unittest.mock import MagicMock

from mne.io import BaseRaw, read_raw_fif  # type: ignore
from pytest import fixture, raises

from metapipe.abc import Processor, Writer, Reader
from metapipe.observer import (
    NodeOut,
    NodeProc,
    NodeIn,
    Observable,
    ObservableNode,
    Observer,
)
from metapipe.tests.test_processors import simple_raw_factory, tmp_raw_savepath, saved_fif_fpath_and_object  #type: ignore # noqa

# from metapipe.tests.


def test_observer_updates_consuming_on_update():
    obs = Observer(callback=lambda: None)
    test_val = True
    obs.update("test", test_val)
    assert obs.consuming["test"] == test_val


def test_observer_calls_update_hook_on_update():
    hook_val = False

    def test_func():
        nonlocal hook_val
        hook_val = True

    obs = Observer(test_func)
    test_val = 42
    obs.update("test", test_val)
    assert hook_val is True


def test_observable_contains_registered_observer():
    observable = Observable()
    observer = Observer(callback=lambda: None)
    observable.register(observer, "test", "test")
    assert observer in observable.observers


def test_observable_doesnt_contain_observer_after_unregister():
    observable = Observable()
    observer = Observer(callback=lambda: None)
    observable.register(observer, "test", "test")
    observable.unregister(observer)
    assert observer not in observable.observers


def test_observable_notifies_registered_observers():
    observable = Observable()
    observer = Observer(callback=lambda: None)
    what, where = "sent", "received"
    observable.register(observer, what, where)
    observable.notify_observers({what: 42})
    assert observer.consuming[where] == 42


@fixture
def mock_processor():
    """Processor which adds 'mock-processed' substring to description"""

    class MockProcessor(Processor):
        """Append somethng to raw.info['description']"""

        class OutSpec(NamedTuple):
            raw: BaseRaw

        def run(self, raw):
            cp = raw.copy()
            if cp.info["description"]:
                cp.info["description"] += ", mock-processed"
            else:
                cp.info["description"] = "mock-processed"

            return self.OutSpec(cp)

    return MockProcessor()


def test_observable_node_attach_registers_observer(mock_processor):
    observable = Observable()
    node = ObservableNode(mock_processor, observable)
    obs_node = NodeOut(mock_processor)
    node.attach(obs_node, "raw", "raw")
    assert obs_node._observer in node._observable.observers


def test_observable_node_attach_raises_if_what_not_in_out_spec(mock_processor):
    observable = Observable()
    node = ObservableNode(mock_processor, observable)
    obs_node = NodeOut(mock_processor)
    what, where = "absent", "raw"
    with raises(AssertionError):
        node.attach(obs_node, what, where)


def test_observable_node_attach_raises_if_where_not_in_out_spec(
    mock_processor,
):
    observable = Observable()
    node = ObservableNode(mock_processor, observable)
    obs_node = NodeOut(mock_processor)
    what, where = "raw", "absent"
    with raises(AssertionError):
        node.attach(obs_node, what, where)


def test_observabole_node_detach(mock_processor):
    observable = Observable()
    node = ObservableNode(mock_processor, observable)
    obs_node = NodeOut(mock_processor)
    what, where = "raw", "raw"
    node.attach(obs_node, what, where)
    node.detach(obs_node)
    assert obs_node._observer not in node._observable.observers


def test_node_proc_runs_only_when_ready(
    mock_processor, simple_raw_factory  # noqa
):
    node = NodeProc(mock_processor)
    node._observable.notify_observers = MagicMock()
    node.run()
    node._observable.notify_observers.assert_not_called()
    raw = simple_raw_factory(1, 200)
    node._observer.consuming["raw"] = raw
    node.run()
    node._observable.notify_observers.assert_called_once()


def test_node_proc_triggers_observers_run(
    mock_processor, simple_raw_factory  # noqa
):
    node1 = NodeProc(mock_processor)
    node2 = NodeProc(mock_processor)
    raw = simple_raw_factory(1, 200)
    node1._observer.consuming["raw"] = raw
    node1.attach(node2, "raw", "raw")
    node2._observable.notify_observers = MagicMock()
    node2._observable.notify_observers.assert_not_called()
    node1.run()
    node2._observable.notify_observers.assert_called_once()


@fixture
def mock_writer():
    @dataclass
    class MockWriter(Writer):
        path: PathLike

        def run(self, raw):
            raw.save(self.path)

    return MockWriter


def test_node_out_runs_only_when_ready(
    mock_writer, simple_raw_factory, tmp_raw_savepath  # noqa
):
    node = NodeOut(mock_writer(tmp_raw_savepath))
    node.run()
    assert not tmp_raw_savepath.exists()
    raw = simple_raw_factory(1, 200)
    node._observer.consuming["raw"] = raw
    node.run()
    assert tmp_raw_savepath.exists()


@fixture
def mock_reader():
    @dataclass
    class MockRawReader(Reader):
        class OutSpec(NamedTuple):
            raw: BaseRaw

        path: PathLike

        def run(self):
            return self.OutSpec(read_raw_fif(self.path, preload=True))

    return MockRawReader


def test_node_in_triggers_observers_run(
    mock_reader, mock_processor, simple_raw_factory, saved_fif_fpath_and_object  # noqa
):
    node1 = NodeIn(mock_reader(saved_fif_fpath_and_object[0]))
    node2 = NodeProc(mock_processor)
    node1.attach(node2, "raw", "raw")
    node2._observable.notify_observers = MagicMock()
    node2._observable.notify_observers.assert_not_called()
    node1.run()
    node2._observable.notify_observers.assert_called_once()
