from collections import OrderedDict

from pytest import fixture, raises

from metapipe.params_tree import (
    ParamsTree,
    LevelError,
    ParamsTreeError,
)


@fixture
def tree():
    return ParamsTree()


def test_tree_contains_added_item_after_appending_layers(tree):
    subjects = ("01", "02", "emptyroom")
    level = "sub"
    tree.append(level, subjects)
    print([i for i in tree._trie])
    for s in subjects:
        assert OrderedDict({"sub": s}) in tree
    tasks = ("eo", "ec")
    tree.append("task", values=tasks)
    runs = ("01", "02", "03")
    tree.append("run", runs)
    for s in subjects:
        for t in tasks:
            for r in runs:
                assert OrderedDict({"sub": s, "task": t, "run": r}) in tree


def test_appending_existing_layer_raises_exception(tree):
    tree.append("root", (None,))
    with raises(LevelError):
        tree.append("root", (None,))


def test_appending_layer_with_nonunique_values_raises_exception(tree):
    with raises(ParamsTreeError):
        tree.append("sub", ("01", "01"))


def test_changing_last_with_nonunique_values_raises_exception(tree):
    tree.append("sub", ("01", "02"))
    with raises(ParamsTreeError):
        tree.change_last(("01", "01"))


def test_change_outermost_level_no_filter(tree):
    tree.append("sub", ("01",))
    tree.append("task", ("eo", "ec"))
    tree.change_last((None,))

    assert OrderedDict((("sub", "01"), ("task", None))) in tree


def test_change_outermost_level_filter(tree):
    tree.append("sub", ("01", "emptyroom"))
    tree.append("task", ("eo",))
    tree.change_last(
        ("noise",), OrderedDict({"sub": "emptyroom"})
    )
    assert OrderedDict({"sub": "01", "task": "eo"}) in tree
    print([i for i in tree._trie])
    assert OrderedDict({"sub": "emptyroom", "task": "noise"}) in tree


def test_change_outermost_level_with_nonexistent_filter_raises_exception(tree):
    tree.append("sub", ("01", "emptyroom"))
    tree.append("task", ("eo",))
    with raises(LevelError):
        tree.change_last(["noise"], {"run": lambda s: s == "01"})


def test_match_prefix(tree):
    tree.append("sub", ("01", "emptyroom"))
    tree.append("task", ("eo", "ec"))
    tree.change_last(["noise"], OrderedDict({"sub": "emptyroom"}))
    tree.append("run", ("01", "02", "03"))
    match = tree.match_prefix(OrderedDict([("sub", "01"), ("task", "ec")]))
    print(match)
    assert match == [
        OrderedDict([("sub", "01"), ("task", "ec"), ("run", "01")]),
        OrderedDict([("sub", "01"), ("task", "ec"), ("run", "02")]),
        OrderedDict([("sub", "01"), ("task", "ec"), ("run", "03")]),
    ]


# def test_print(tree):
#     tree.append("sub", ("01", "emptyroom"))
#     tree.append("task", ("eo", "ec"))
#     INDENT = " " * 4
#     SEP = ": "
#     assert str(tree) == (
#         f"sub{SEP}01\n"
#         + f"{INDENT}task{SEP}eo\n"
#         + f"{INDENT}task{SEP}ec\n"
#         + f"sub{SEP}emptyroom\n"
#         + f"{INDENT}task{SEP}eo\n"
#         + f"{INDENT}task{SEP}ec"
#     )
