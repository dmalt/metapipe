from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Iterable, List


class LevelError(Exception):
    pass


@dataclass
class ParamsTreeNode:
    level: str
    value: Any
    _children: list = field(default_factory=list, init=False, repr=False)

    @property
    def children(self):
        return self._children

    @classmethod
    def _create_level(cls, level_name, values):
        return [cls(level_name, v) for v in values]

    def flatten_keys(self) -> Iterable[OrderedDict]:
        if self._is_leaf_node():
            yield OrderedDict({self.level: self.value})
        for c in self.children:
            for k in c.flatten_keys():
                yield {self.level: self.value} | k

    def _change_outermost_level(self, level_name, values, filt: dict):
        if self._is_next_to_leaf_node():
            self._children = self._create_level(level_name, values)
        else:
            for c in filter(lambda c: c.level not in filt or filt[c.level](c.value), self.children):
                c._change_outermost_level(level_name, values, filt)

    def _append_level(self, level_name, values):
        if self._is_leaf_node():
            self._children = self._create_level(level_name, values)
        else:
            for c in self.children:
                c._append_level(level_name, values)

    def _is_leaf_node(self):
        return not self._children

    def _is_next_to_leaf_node(self):
        return self._children and not self.children[0]._children


@dataclass
class ParamsTree(ParamsTreeNode):
    _level_names: List[str] = field(init=False, repr=False)

    @property
    def level_names(self):
        return self._level_names

    def __post_init__(self):
        self._level_names = [self.level]

    def append_level(self, level_name, values):
        if level_name in self.level_names:
            raise LevelError(f"Level '{level_name}' exists")
        self._append_level(level_name, values)
        self._level_names.append(level_name)

    def change_outermost_level(self, level_name, values, filt):
        self._check_filter_levels(filt)
        self._change_outermost_level(level_name, values, filt)

    def _check_filter_levels(self, filt):
        for level in filt:
            if level not in self._level_names:
                raise LevelError(f"Level {level} not found")
