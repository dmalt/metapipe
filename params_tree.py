from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Iterable, List, Collection
from itertools import chain


INDENT = " " * 4
SEP = ": "


class LevelError(Exception):
    pass


@dataclass
class _ParamsTreeNode:
    level: str
    value: Any
    _children: List = field(default_factory=list, init=False, repr=False)

    @property
    def children(self):
        return self._children

    def flatten(self) -> Iterable[OrderedDict]:
        if self.is_leaf_node():
            yield OrderedDict({self.level: self.value})
        for c in self.children:
            for k in c.flatten():
                yield {self.level: self.value} | k

    def change_last_level(self, values, level_filters: dict = None):
        level_filters = {} if level_filters is None else level_filters
        if self.is_next_to_leaf_node():
            self._children = self._create_level(self.children[0].level, values)
        else:
            for c in self._filt_children(level_filters):
                c.change_last_level(values, level_filters)

    def append_level(self, level_name, values):
        if self.is_leaf_node():
            self._children = self._create_level(level_name, values)
        else:
            for c in self.children:
                c.append_level(level_name, values)

    def is_leaf_node(self):
        return not self._children

    def is_next_to_leaf_node(self):
        return self._children and not self.children[0]._children

    def __str__(self):
        res = [f"{self.level}{SEP}{self.value}"]
        if not self.is_leaf_node():
            res.append("\n".join(self._indent(str(c)) for c in self.children))
        return "\n".join(res)

    @staticmethod
    def _indent(node_str):
        return "\n".join(map(lambda k: INDENT + k, node_str.split("\n")))

    @classmethod
    def _create_level(cls, level_name, values):
        return [cls(level_name, v) for v in values]

    def _filt_children(self, filt):
        return filter(
            lambda c: c.level not in filt or filt[c.level](c.value),
            self.children,
        )


@dataclass
class ParamsTree:
    _levels: List[str] = field(init=False, repr=False, default_factory=list)
    _root: _ParamsTreeNode = field(init=False, repr=False)

    @property
    def levels(self):
        return self._levels

    def __post_init__(self):
        self._root = _ParamsTreeNode("ROOT", None)

    def flatten(self) -> Iterable[OrderedDict]:
        """Iterate over flattened tree"""
        return chain(*(c.flatten() for c in self._root.children))

    def append(self, level_name: str, values: Collection[Any]):
        """Append level to a tree"""
        if level_name in self.levels:
            raise LevelError(f"Level '{level_name}' exists")
        self._root.append_level(level_name, values)
        self._levels.append(level_name)

    def change_last(self, values: Collection[Any], level_filters=None):
        """Selectively change last level values"""
        self._check_filter_levels_present(level_filters)
        self._root.change_last_level(values, level_filters)

    def __str__(self):
        return "\n".join(str(c) for c in self._root.children)

    def _check_filter_levels_present(self, level_filters):
        if level_filters is None:
            return
        if any(level for level in level_filters if level not in self._levels):
            raise LevelError("One of filter levels not found")
