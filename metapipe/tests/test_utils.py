from metapipe.utils import make_task
from metapipe.tests.test_interfaces import MockFileProcessor  # noqa


def test_make_task_returns_proper_dict(MockFileProcessor):  # noqa
    builder = MockFileProcessor.Builder()
    node = builder.with_deps("in.fif").with_targets("out.fif").build()
    task = make_task(node, name="test", clean=False)
    assert task == dict(
        name="test",
        file_dep=["in.fif"],
        actions=[node.run],
        targets=["out.fif"],
        clean=False,
    )
