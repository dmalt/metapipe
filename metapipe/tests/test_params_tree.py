from collections import OrderedDict

from pytest import fixture, raises

from metapipe.params_tree import (
    ParamsTree,
    LevelError,
    FlatView,
    ParamsNode,
    ParamsTreeError,
)


@fixture
def tree():
    return ParamsTree()


def test_params_node_getitem_raises_exception_when_no_item(tree):
    with raises(ParamsTreeError):
        tree.root["something"]


def test_add_single_layer_sets_children_and_appends_level_name(tree):
    subjects = ("01", "02", "emptyroom")
    level = "sub"
    tree.append(level, subjects)
    assert tree.levels[-1] == level
    for s in subjects:
        assert tree.root[s] == ParamsNode(level, s)


def test_appending_existing_layer_raises_exception(tree):
    tree.append("root", (None,))
    with raises(LevelError):
        tree.append("root", (None,))


def test_change_outermost_level_no_filter(tree):
    tree.append("sub", ("01",))
    tree.append("task", ("eo", "ec"))
    tree.change_last((None,))

    assert tree.root["01"][None] == ParamsNode("task", None)


def test_change_outermost_level_filter(tree):
    tree.append("sub", ("01", "emptyroom"))
    tree.append("task", ("eo",))
    tree.change_last(
        ("noise",), level_filters={"sub": lambda s: s == "emptyroom"}
    )
    keys = FlatView().get(tree)
    assert keys == [
        OrderedDict({"sub": "01", "task": "eo"}),
        OrderedDict({"sub": "emptyroom", "task": "noise"}),
    ]


def test_change_outermost_level_with_nonexistent_filter_raises_exception(tree):
    tree.append("sub", ("01", "emptyroom"))
    tree.append("task", ("eo",))
    with raises(LevelError):
        tree.change_last(["noise"], {"run": lambda s: s == "01"})


def test_print(tree):
    tree.append("sub", ("01", "emptyroom"))
    tree.append("task", ("eo", "ec"))
    INDENT = " " * 4
    SEP = ": "
    assert str(tree) == (
        f"sub{SEP}01\n"
        + f"{INDENT}task{SEP}eo\n"
        + f"{INDENT}task{SEP}ec\n"
        + f"sub{SEP}emptyroom\n"
        + f"{INDENT}task{SEP}eo\n"
        + f"{INDENT}task{SEP}ec"
    )