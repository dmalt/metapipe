from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Callable, Union

from metapipe.abc import Reader, Writer, Processor
from inspect import signature


@dataclass
class Observer:
    callback: Callable[[], None]
    consuming: Dict[str, object] = field(default_factory=dict)

    def update(self, key: str, value: Any) -> None:
        self.consuming[key] = value
        self.callback()


@dataclass
class Observable:
    _observers: List[Tuple[Observer, str, str]] = field(
        init=False, repr=False, default_factory=list
    )

    def register(self, observer: Observer, what: str, where: str) -> None:
        self._observers.append((observer, what, where))

    def unregister(self, observer: Observer) -> None:
        self._observers = [o for o in self._observers if o[0] != observer]

    def notify_observers(self, providing: Dict) -> None:
        for obs, what, where in self._observers:
            obs.update(where, providing[what])

    @property
    def observers(self):
        return [o[0] for o in self._observers]


ObserverNode = Union["NodeProc", "NodeOut"]


@dataclass
class ObservableNode:
    processor: Union[Reader, Processor]
    _observable: Observable

    def attach(self, node: ObserverNode, what: str, where: str) -> None:
        assert what in self.processor.OutSpec._fields
        assert where in signature(node.processor.run).parameters
        self._observable.register(node._observer, what, where)

    def detach(self, node: ObserverNode) -> None:
        self._observable.unregister(node._observer)


@dataclass
class NodeProc(ObservableNode):
    processor: Processor
    _observable: Observable = field(
        init=False, repr=False, default_factory=Observable
    )
    _observer: Observer = field(init=False, repr=False)

    def __post_init__(self):
        self._observer = Observer(callback=self.run)

    def run(self) -> None:
        try:
            res = self.processor.run(**self._observer.consuming)._asdict()
            self._observable.notify_observers(res)
            self._observer.consuming = {}
        except TypeError:
            pass


@dataclass
class NodeOut:
    processor: Writer
    _observer: Observer = field(init=False, repr=False)

    def __post_init__(self):
        self._observer = Observer(callback=self.run)

    def run(self) -> None:
        try:
            self.processor.run(**self._observer.consuming)
            self._observer.consuming = {}
        except TypeError:
            pass


@dataclass
class NodeIn(ObservableNode):
    processor: Reader
    _observable: Observable = field(
        init=False, repr=False, default_factory=Observable
    )

    def run(self) -> None:
        res = self.processor.run()._asdict()
        self._observable.notify_observers(res)
