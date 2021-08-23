from collections import OrderedDict

from pytest import fixture, raises

from metapipe.params_tree import ParamsTrie, ParamsTrieError


@fixture
def trie():
    return ParamsTrie()


def test_new_trie_is_created_empty():
    assert len(ParamsTrie()) == 0
