from collections import OrderedDict

from pytest import fixture, raises

from params_tree import ParamsTree, LevelError


@fixture
def tree_factory():
    def wrapped(level, value):
        return ParamsTree(level=level, value=None)

    return wrapped


def test_constuctor_sets_attributes(tree_factory):
    tree = tree_factory(level="root", value=None)
    assert tree.level == "root"
    assert tree.value is None
    assert tree.level_names == ["root"]


def test_add_single_layer_sets_children_and_appends_level_name(tree_factory):
    subjects = ("01", "02", "emptyroom")
    level = "sub"
    tree = tree_factory(level="root", value=None)
    tree.append_level(level, subjects)
    assert tree.level_names[-1] == level
    for child in tree.children:
        assert child.level == level
        assert child.value in subjects


def test_appending_existing_layer_raises_exception(tree_factory):
    tree = tree_factory("root", None)
    with raises(LevelError):
        tree.append_level("root", (None,))


def test_flatten_keys(tree_factory):
    tree = tree_factory(level="root", value=None)
    subjects = ("01", "02", "emptyroom")
    level = "sub"
    tree.append_level(level, subjects)
    flat_keys = list(tree.flatten_keys())
    assert flat_keys == [
        OrderedDict({"root": None, "sub": "01"}),
        OrderedDict({"root": None, "sub": "02"}),
        OrderedDict({"root": None, "sub": "emptyroom"}),
    ]


def test_change_outermost_level_no_filter(tree_factory):
    tree = tree_factory("root", None)
    tree.append_level("sub", ("01",))
    tree.append_level("task", ("eo", "ec"))
    tree.change_outermost_level((None,), filt={})

    keys = list(tree.flatten_keys())
    assert keys == [OrderedDict({"root": None, "sub": "01", "task": None})]


def test_change_outermost_level_filter(tree_factory):
    tree = tree_factory("root", None)
    tree.append_level("sub", ("01", "emptyroom"))
    tree.append_level("task", ("eo",))
    tree.change_outermost_level(
        ("noise",), filt={"sub": lambda s: s == "emptyroom"}
    )
    keys = list(tree.flatten_keys())
    assert keys == [
        OrderedDict({"root": None, "sub": "01", "task": "eo"}),
        OrderedDict({"root": None, "sub": "emptyroom", "task": "noise"}),
    ]


def test_change_outermost_level_with_nonexistent_filter_raises_exception(tree_factory):
    tree = tree_factory("root", None)
    tree.append_level("sub", ("01", "emptyroom"))
    tree.append_level("task", ("eo",))
    with raises(LevelError):
        tree.change_outermost_level(
            values=["noise"], filt={"run": lambda s: s == "01"}
        )
