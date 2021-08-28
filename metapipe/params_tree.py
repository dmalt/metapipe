from functools import wraps
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from itertools import product, repeat, chain
from typing import Any, Callable, Collection, Dict, List


class ParamsTreeError(Exception):
    pass


class LevelError(ParamsTreeError):
    pass


# class ViewableTree(ABC):
#     root: ViewableNode = field(init=False, repr=False)


# class View(ABC):
#     @abstractmethod
#     def get(self, tree: ViewableTree) -> Any:
#         """Get the view"""


# class FlatView(View):
#     def get(self, tree: ViewableTree) -> List[OrderedDict]:
#         return list(chain(*(self.flatten(c) for c in tree.root.children)))

#     @staticmethod
#     def flatten(node: ViewableNode) -> Generator[OrderedDict, None, None]:
#         if node.is_leaf_node():
#             yield OrderedDict({node.level: node.value})
#         for c in node.children:
#             for k in FlatView.flatten(c):
#                 yield OrderedDict({node.level: node.value} | k)


# @dataclass
# class StringView(View):
#     TAB: str = " " * 4
#     SEP: str = ": "

#     def get(self, tree: ViewableTree) -> str:
#         return "\n".join(self._to_str(c) for c in tree.root.children)

#     def _to_str(self, node: ViewableNode) -> str:
#         res = [f"{node.level}{self.SEP}{node.value}"]
#         res.extend(self._indent(self._to_str(c)) for c in node.children)
#         return "\n".join(res)

#     def _indent(self, node_str: str) -> str:
#         return "\n".join(map(lambda k: self.TAB + k, node_str.split("\n")))


def ensure_first_arg_is_not_none(func):
    @wraps(func)
    def wrapped(self, first, *rest):
        if first is None:
            raise ValueError(f"argument to {func.__name__}() is None")
        return func(self, first, *rest)

    return wrapped


@dataclass
class Trie:
    @dataclass
    class _Node:
        value: Any = field(init=False, default=None)
        children: dict = field(
            default_factory=lambda: defaultdict(lambda: None)
        )

    _root: "_Node" = field(default=None, init=False, repr=False)
    _n_keys: int = field(default=0, init=False, repr=False)

    def __contains__(self, key: OrderedDict) -> bool:
        return self.get(key) is not None

    def __len__(self) -> int:
        return self._n_keys

    def __iter__(self) -> List[OrderedDict]:
        results: List = []
        self._collect(self._root, results, OrderedDict())
        return iter(results)

    @ensure_first_arg_is_not_none
    def get(self, key: OrderedDict, /) -> Any:
        node = self._get(self._root, key.copy())
        return None if node is None else node.value

    @ensure_first_arg_is_not_none
    def put(self, key: OrderedDict, value: Any, /) -> None:
        if value is None:
            self.delete(key)
        else:
            self._root = self._put(self._root, key.copy(), value)

    @ensure_first_arg_is_not_none
    def delete(self, key: OrderedDict, /):
        self._root = self._delete(self._root, key.copy())

    def match_prefix(self, prefix: OrderedDict) -> List[OrderedDict]:
        node = self._get(self._root, prefix)
        results = []
        self._collect(node, results, OrderedDict())
        return results

    def match(self, pattern: OrderedDict) -> List[OrderedDict]:
        results = []
        self._match(self._root, OrderedDict(), pattern.copy(), results)
        return results

    def _get(self, node, key):
        if node is None or not key:
            return node
        item = key.popitem(last=False)
        return self._get(node.children[item], key)

    def _put(self, node, key, value):
        if node is None:
            node = self._Node()
        if not key:
            if node.value is None:
                self._n_keys += 1
            node.value = value
            return node
        item = key.popitem(last=False)
        node.children[item] = self._put(node.children[item], key, value)
        return node

    def _delete(self, node, key):
        if node is None:
            return None
        if not key:
            if node.value is not None:
                self._n_keys -= 1
            node.value = None
        else:
            item = key.popitem(last=False)
            node.children[item] = self._delete(node.children[item], key)

        # remove subtrie rooted at node if it is completely empty
        if node.value is not None:
            return node
        for item in node.children:
            if node.children[item] is not None:
                return node
        return None

    def _collect(self, node, results, prefix):
        if node is None:
            return
        if node.value is not None:
            results.append(prefix.copy())

        for item in node.children:
            prefix[item[0]] = item[1]
            self._collect(node.children[item], results, prefix)
            prefix.popitem()

    def _match(self, node, prefix, pattern, results):
        if node is None:
            return
        if not pattern and node.value is not None:
            results.append(prefix.copy())
        if not pattern:
            return
        item = pattern.popitem(last=False)
        if item[1] == "*":
            for c in node.children:
                prefix[c[0]] = c[1]
                self._match(node.children[c], prefix, pattern.copy(), results)
                prefix.popitem()
        else:
            prefix[item[0]] = item[1]
            self._match(node.children[item], prefix, pattern, results)
            prefix.popitem()


@dataclass
class ParamsTree:

    _levels: List[str] = field(init=False, repr=False, default_factory=list)
    _trie: Trie = field(init=False, repr=False, default_factory=Trie)

    def append(self, level_name: str, values: Collection[str]) -> None:
        """Append level to a tree"""
        if level_name in self._levels:
            raise LevelError(f"Level '{level_name}' exists")
        self._check_values_unique(values)
        self._append(level_name, values)
        self._levels.append(level_name)

    def __contains__(self, key):
        return key in self._trie

    def collect_till(self, depth=None):
        levels = self._levels if depth is None else self._levels[:depth]
        return self._trie.match(OrderedDict([(d, "*") for d in levels]))

    def change_last(self, values: Collection[str], prefix=None) -> None:
        """Selectively change last level values"""
        level_filters = OrderedDict({}) if prefix is None else prefix
        self._check_filter_levels_present(level_filters)
        self._check_values_unique(values)
        self._change_last(values, level_filters)

    def match_prefix(self, prefix):
        vals = prefix.values()
        match = self._trie.match(
            OrderedDict(
                [tup for tup in zip(self._levels, chain(vals, repeat("*")))]
            )
        )
        return match

    def _append(self, level_name, values):
        if not self._trie:
            for v in values:
                self._trie.put(OrderedDict({level_name: v}), True)
        for key, v in product(self.collect_till(), values):
            new_key = key.copy()
            new_key[level_name] = v
            self._trie.put(new_key, True)

    def _change_last(self, values, prefix):
        for key in self.match_prefix(prefix):
            self._trie.delete(key)
            level, _ = key.popitem()
            for v in values:
                copy = key.copy()
                copy[level] = v
                self._trie.put(copy, True)

    def _check_filter_levels_present(self, level_filters):
        if any(level for level in level_filters if level not in self._levels):
            raise LevelError(
                f"Each filter level must be one of {self._levels}"
            )

    @staticmethod
    def _check_values_unique(values) -> None:
        if len(set(values)) != len(values):
            raise ParamsTreeError(
                f"All values must be different (got '{values}')"
            )
