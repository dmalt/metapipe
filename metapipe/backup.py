import os
import os.path as op
from filecmp import cmp, dircmp
from pathlib import Path
from shutil import copy2, copytree, rmtree
from dataclasses import dataclass

from doit.cmd_base import DoitCmdBase, check_tasks_exist  # type: ignore
from doit.control import TaskControl  # type: ignore


def get_common_parent(paths):
    if len(paths) == 1:
        src = paths[0].parent
    else:
        src = Path(op.commonpath(paths))
    assert src.is_dir()
    return src


def flatten_dir(src_path):
    for root, dirs, files in os.walk(src_path):
        for f in files:
            yield Path(root).resolve() / f


opt_backup_dest = {
    "name": "dest_dir",
    "short": "t",
    "long": "dest",
    "type": str,
    "default": "../backup",
    "help": "destination folder",
}

opt_backup_dryrun = {
    "name": "dryrun",
    "short": "n",
    "long": "dry-run",
    "type": bool,
    "default": False,
    "help": "print actions without really executing them",
}


@dataclass
class BackupManager:
    src_dir: Path
    dest_dir: Path
    dryrun: bool

    def backup_file(self, src, dst, shallow=True):
        if dst.exists():
            assert dst.is_file(), f"Destination {dst} is not a file"
            if cmp(src, dst, shallow):
                print(f"{dst} is uptodate. Skipping.")
                return
        print(f"{src} --> {dst}")
        if not self.dryrun:
            dst.parent.mkdir(exist_ok=True, parents=True)
            copy2(src, dst)

    def backup_dirs(self, src, dest):
        self._backup_dirs(dircmp(src, dest))

    def _backup_dirs(self, dircmp_inst):
        self._backup_left(dircmp_inst)
        self._backup_right(dircmp_inst)
        self._backup_common(dircmp_inst)
        for subdircmp in dircmp.subdirs.values():
            self._backup_dirs(subdircmp)

    def _backup_common(self, dircmp_inst):
        for f in dircmp.common_files:
            s = Path(dircmp_inst.left) / f
            d = self.dest_dir / s.relative_to(self.src_dir)
            self.backup_file(s, d)

    def _backup_right(self, dircmp_inst):
        for f in dircmp_inst.right_only:
            d = Path(dircmp_inst.right) / f
            if d.is_file():
                print(f"Removing file: '{d}'")
                if not self.dryrun:
                    d.unlink()
            elif d.is_dir():
                print(f"Removing folder: '{d}'")
                if not self.dryrun:
                    rmtree(d)
            else:
                raise ValueError(f"{d} is neither a file nor a directory")

    def _backup_left(self, dircmp_inst):
        for f in dircmp_inst.left_only:
            s = Path(dircmp_inst.left) / f
            d = self.dest_dir / s.relative_to(self.src_dir)
            if s.is_file():
                print(f"{s} --> {d}")
                if not self.dryrun:
                    d.parent.mkdir(exist_ok=True, parents=True)
                    copy2(s, d)
            elif s.is_dir():
                copytree(s, d)
            else:
                raise ValueError(f"{s} is neither a file nor a directory")


class Backup(DoitCmdBase):
    doc_purpose = "backup data"
    doc_usage = ""
    doc_description = """Backup data"""

    cmd_options = (opt_backup_dest, opt_backup_dryrun)

    def _execute(self, dest_dir, dryrun, pos_args=None):
        tasks, selected = self.task_list, pos_args
        dest_dir = Path(dest_dir).resolve()

        backup_tasks = (
            filter(lambda t: t.name in selected, tasks) if selected else tasks
        )

        backup_paths = self._get_paths_4_backup(backup_tasks)
        if not backup_paths:
            return
        src_dir = get_common_parent(backup_paths)
        print(backup_paths)

        backup_manager = BackupManager(src_dir, dest_dir, dryrun)

        for src_path in backup_paths:
            d = dest_dir / src_path.relative_to(src_dir)
            if src_path.is_file():
                backup_manager.backup_file(src_path, d)
            elif src_path.is_dir():
                d.mkdir(exist_ok=True, parents=True)
                backup_manager.backup_dirs(src_path, d)

    def _check_tasks(self, selected_tasks):
        tasks = TaskControl(self.task_list).tasks
        check_tasks_exist(tasks, selected_tasks)

    @staticmethod
    def _get_paths_4_backup(backup_tasks, ignore_clean=True):
        src_paths = []
        for task in backup_tasks:
            if ignore_clean and task._remove_targets:
                continue
            for t in map(lambda x: Path(x).resolve(), task.targets):
                if t.exists():
                    src_paths.append(t)
        return src_paths
