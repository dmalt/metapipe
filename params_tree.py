from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Iterable, List, Collection
from itertools import chain
from abc import ABC, abstractmethod


class LevelError(Exception):
    pass


@dataclass
class ViewableParamsNode:
    level: str
    value: Any
    children: List = field(default_factory=list, init=False, repr=False)

    def is_leaf_node(self):
        return not self.children

    def is_next_to_leaf_node(self):
        return self.children and not self.children[0].children


@dataclass
class ViewableTree(ABC):
    root: ViewableParamsNode = field(init=False, repr=False)


class View(ABC):
    @abstractmethod
    def get(self, tree: ViewableTree):
        """Get the view"""


class FlatView(View):
    def get(self, tree):
        return list(chain(*(self.flatten(c) for c in tree.root.children)))

    @staticmethod
    def flatten(node) -> Iterable[OrderedDict]:
        if node.is_leaf_node():
            yield OrderedDict({node.level: node.value})
        for c in node.children:
            for k in FlatView.flatten(c):
                yield {node.level: node.value} | k


@dataclass
class StringView(View):
    TAB: str = " " * 4
    SEP: str = ": "

    def get(self, tree):
        return "\n".join(self._to_str(c) for c in tree.root.children)

    def _to_str(self, node):
        res = [f"{node.level}{self.SEP}{node.value}"]
        res.extend(self._indent(self._to_str(c)) for c in node.children)
        return "\n".join(res)

    def _indent(self, node_str) -> str:
        return "\n".join(map(lambda k: self.TAB + k, node_str.split("\n")))


class ParamsNode(ViewableParamsNode):
    @classmethod
    def create_level(cls, level_name, values) -> List:
        return [cls(level_name, v) for v in values]


@dataclass
class ParamsTree(ViewableTree):
    root: ParamsNode = field(init=False, repr=False)
    str_view: StringView = field(default_factory=StringView)
    levels: List[str] = field(init=False, repr=False, default_factory=list)

    def __post_init__(self):
        self.root = ParamsNode("ROOT", None)

    def append(self, level_name: str, values: Collection[Any]):
        """Append level to a tree"""
        if level_name in self.levels:
            raise LevelError(f"Level '{level_name}' exists")
        self.levels.append(level_name)
        self._append(self.root, level_name, values)

    def change_last(self, values: Collection[Any], level_filters=None):
        """Selectively change last level values"""
        level_filters = {} if level_filters is None else level_filters
        self._check_filter_levels_present(level_filters)
        self._change_last(self.root, values, level_filters)

    def __str__(self):
        return self.str_view.get(self)

    def _append(self, node, level_name, values):
        if node.is_leaf_node():
            node.children = self.root.create_level(level_name, values)
        else:
            for child in node.children:
                self._append(child, level_name, values)

    def _change_last(self, node, values, level_filters):
        if node.is_next_to_leaf_node():
            node.children = node.create_level(node.children[0].level, values)
        else:
            for c in self.filt_children(node, level_filters):
                self._change_last(c, values, level_filters)

    def _check_filter_levels_present(self, level_filters):
        if any(level for level in level_filters if level not in self.levels):
            raise LevelError(f"Each filter level must be one of {self.levels}")

    @staticmethod
    def filt_children(node, filt) -> Iterable:
        return filter(
            lambda c: c.level not in filt or filt[c.level](c.value),
            node.children,
        )
