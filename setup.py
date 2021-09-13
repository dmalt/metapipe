from setuptools import setup

setup(
    name="metapipe",
    version="0.0.1",
    author="Dmitrii Altukhov",
    author_email="dm.altukhov@ya.ru",
    packages=["metapipe"],
    entry_points={"doit.COMMAND": ["backup = metapipe.backup:Backup"]},
)
