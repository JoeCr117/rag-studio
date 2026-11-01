"""Where a registered Windows path appears inside the worker, which sees every host drive read-only under one mount.

Docker Desktop exposes host drives at `/run/desktop/mnt/host/<drive letter>`; compose.yaml mounts that folder into the
worker. Because the mount itself always exists, a missing source folder is an ordinary "not found", never a failed
container start.
"""

from pathlib import PurePath, PureWindowsPath


class InvalidHostPath(ValueError):
    pass


def container_path[P: PurePath](host_path: str, drives_root: P) -> P:
    """`W:\\Docs\\Notes` -> `<drives_root>/w/Docs/Notes`. Drive letters are lowercase there; the rest keeps its case."""
    path = PureWindowsPath(host_path)
    if path.drive.startswith("\\\\"):
        raise InvalidHostPath(
            "Network paths cannot be sources: Docker sees only this PC's local drives. "
            f"Copy the folder to a local drive: {host_path}"
        )
    if len(path.drive) != 2 or not path.drive[0].isalpha() or not path.is_absolute():
        raise InvalidHostPath(f"Not an absolute Windows path with a drive letter: {host_path}")
    if ".." in path.parts:
        raise InvalidHostPath(f"Path must not contain '..': {host_path}")
    return drives_root.joinpath(path.drive[0].lower(), *path.parts[1:])
