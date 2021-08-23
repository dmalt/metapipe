from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Sequence, Union

Value = Union[str, int, None]


class ParamsTrieError(Exception):
    pass


@dataclass
class ParamsTrie:
    @dataclass
    class _ParamsNode:
        key: str
        value: Value
        children: Sequence

    _root: _ParamsNode = field(init=False, repr=False)

    def __post_init__(self):
        self.root = self._ParamsNode("ROOT", None, [])

    def __len__(self):
        return 0
