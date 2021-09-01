from metapipe import abc


def make_task(node: abc.FileProcessor, name: str, clean=False) -> dict:
    """Produce doit task"""
    return dict(
        name=name,
        file_dep=node.deps,
        actions=[node.run],
        targets=node.targets,
        clean=clean,
    )

# def make_task(self, name) -> dict:
#     from doit.tools import config_changed  # type: ignore

#     base_dict = super().make_task(name)
#     base_dict["uptodate"] = [config_changed(self.config)]
#     return base_dict
