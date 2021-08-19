from collections import OrderedDict

from pytest import fixture, raises

from params_tree import ParamsTree, LevelError, INDENT, SEP


@fixture
def tree():
    return ParamsTree()


def test_add_single_layer_sets_children_and_appends_level_name(tree):
    subjects = ("01", "02", "emptyroom")
    level = "sub"
    tree.append(level, subjects)
    assert tree.level_names[-1] == level
    flat_keys = list(tree.flatten())
    assert flat_keys == [OrderedDict({"sub": s}) for s in subjects]


def test_appending_existing_layer_raises_exception(tree):
    tree.append("root", (None,))
    with raises(LevelError):
        tree.append("root", (None,))


def test_change_outermost_level_no_filter(tree):
    tree.append("sub", ("01",))
    tree.append("task", ("eo", "ec"))
    tree.change_last((None,))

    keys = list(tree.flatten())
    assert keys == [OrderedDict({"sub": "01", "task": None})]


def test_change_outermost_level_filter(tree):
    tree.append("sub", ("01", "emptyroom"))
    tree.append("task", ("eo",))
    tree.change_last(
        ("noise",), level_filters={"sub": lambda s: s == "emptyroom"}
    )
    keys = list(tree.flatten())
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
    assert str(tree) == (
        f"sub{SEP}01\n"
        + f"{INDENT}task{SEP}eo\n"
        + f"{INDENT}task{SEP}ec\n"
        + f"sub{SEP}emptyroom\n"
        + f"{INDENT}task{SEP}eo\n"
        + f"{INDENT}task{SEP}ec"
    )
