from pytest import fixture, raises  # type: ignore
from pathlib import Path
from shutil import copy2

from metapipe.backup import BackupManager, BackupActions


@fixture
def backup_manager(tmp_path: Path):
    src_dir = tmp_path / "src_dir"
    src_dir.mkdir()
    dest_dir = tmp_path / "backup"
    dest_dir.mkdir(exist_ok=True)
    return BackupManager(src_dir, dest_dir, dryrun=False)


def test_backup_file_raises_file_not_found_if_src_doesnt_exist(backup_manager):
    src = backup_manager.src_dir / "new_file.tmp"
    dst = backup_manager.dest_dir / "new_file.tmp"

    with raises(FileNotFoundError):
        backup_manager.backup_file(src, dst)


def test_backup_file_overwrites_if_dst_exists_and_is_a_dir(backup_manager):
    src = backup_manager.src_dir / "new_file.tmp"
    src.touch()
    dst = backup_manager.dest_dir / "new_file.tmp"
    dst.mkdir()
    assert BackupActions.OVERWRITE_FILE == backup_manager.backup_file(src, dst)
    assert dst.is_file()


def test_backup_file_backs_up_new_file(backup_manager: BackupManager):
    src = backup_manager.src_dir / "new_file.tmp"
    src.touch()
    dst = backup_manager.dest_dir / "new_file.tmp"

    assert not dst.exists()
    assert BackupActions.COPY_FILE == backup_manager.backup_file(src, dst)
    assert dst.exists()


def test_backup_file_skips_existing_file(backup_manager):
    src = backup_manager.src_dir / "new_file.tmp"
    src.touch()
    dst = backup_manager.dest_dir / "new_file.tmp"
    copy2(src, dst)

    assert BackupActions.SKIP_FILE == backup_manager.backup_file(src, dst)


def test_backup_dir_raises_file_not_found_if_src_doesnt_exist(backup_manager):
    src = backup_manager.src_dir / "dir_to_backup"
    dst = backup_manager.dest_dir / "dir_to_backup"
    with raises(FileNotFoundError):
        backup_manager.backup_dir(src, dst)


def test_backup_dir_creates_dst_if_it_doesnt_exist(backup_manager):
    src = backup_manager.src_dir / "dir_to_backup"
    src.mkdir()
    dst = backup_manager.dest_dir / "dir_to_backup"
    backup_manager.backup_dir(src, dst)
    assert dst.exists()


def test_backup_dir_overwrites_notadir_if_dst_exists_is_file(backup_manager):
    src = backup_manager.src_dir / "dir_to_backup"
    src.mkdir()
    dst = backup_manager.dest_dir / "dir_to_backup"
    dst.touch()
    actions = backup_manager.backup_dir(src, dst)
    assert actions[(str(src), str(dst))] == BackupActions.OVERWRITE_FILE
    assert dst.is_dir()


def test_backup_dir_copies_not_backed_up_files(backup_manager):
    src = backup_manager.src_dir / "dir_to_backup"
    src.mkdir()
    dst = backup_manager.dest_dir / "dir_to_backup"
    src_fpath = src / "file1"
    src_fpath.touch()
    dst_fpath = dst / "file1"
    actions = backup_manager.backup_dir(src, dst)
    assert actions[(str(src_fpath), str(dst_fpath))] == BackupActions.COPY_FILE
    assert (dst / "file1").exists()


def test_backup_dir_removes_extra_files(backup_manager):
    src = backup_manager.src_dir / "dir_to_backup"
    src.mkdir()
    dst = backup_manager.dest_dir / "dir_to_backup"
    dst.mkdir()
    (dst / "file2").touch()
    (dst / "dir1").mkdir()
    (dst / "dir1" / "file3").touch()
    actions = backup_manager.backup_dir(src, dst)
    assert actions[("", str(dst / "file2"))] == BackupActions.REMOVE_FILE
    assert actions[("", str(dst / "dir1"))] == BackupActions.REMOVE_DIR
    assert not (dst / "file2").exists()
    assert not (dst / "dir1").exists()


def test_backup_dir_backups_common_files(backup_manager):
    src = backup_manager.src_dir / "dir_to_backup"
    src.mkdir()
    dst = backup_manager.dest_dir / "dir_to_backup"
    dst.mkdir()
    (src / "f1").touch()
    copy2(src / "f1", dst / "f1")
    (src / "dir1").mkdir()
    (src / "dir1" / "f2").touch()
    (dst / "dir1").mkdir()
    (dst / "dir1" / "f2").touch()
    with open(dst / "dir1" / "f2", "w") as f:
        f.write("test")
    actions = backup_manager.backup_dir(src, dst)
    assert (
        actions[(str(src / "f1"), str(dst / "f1"))] == BackupActions.SKIP_FILE
    )
    assert (
        actions[(str(src / "dir1" / "f2"), str(dst / "dir1" / "f2"))]
        == BackupActions.OVERWRITE_FILE
    )
