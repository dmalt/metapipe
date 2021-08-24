from collections import OrderedDict

from pytest import fixture

from metapipe.params_tree import ParamsTrie


@fixture
def trie():
    return ParamsTrie()


@fixture
def item():
    return OrderedDict([("sub", "01")])


def test_new_trie_is_created_empty():
    assert len(ParamsTrie()) == 0


def test_putting_item_in_empty_trie_incriments_len(trie, item):
    assert len(trie) == 0
    trie.put(item)
    assert len(trie) == 1


def test_trie_contains_put_item(trie, item):
    trie.put(item)
    assert item in trie


# def test_trie_doesnt_contain_item_that_hasnt_been_added(trie, item):
#     assert item not in trie
