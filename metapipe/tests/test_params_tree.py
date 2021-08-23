from collections import OrderedDict

from pytest import fixture, raises

from metapipe.params_tree import ParamsTrie, ParamsTrieError


@fixture
def tree():
    return ParamsTrie()
