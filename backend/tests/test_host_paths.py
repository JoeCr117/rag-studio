from pathlib import PurePosixPath

import pytest

from studio.sources.host_paths import InvalidHostPath, container_path

DRIVES = PurePosixPath("/host")


def test_windows_paths_map_under_the_lowercase_drive_letter():
    assert container_path(r"W:\Projects\My Notes", DRIVES) == PurePosixPath("/host/w/Projects/My Notes")
    assert container_path("C:/Users/Alex", DRIVES) == PurePosixPath("/host/c/Users/Alex")
    assert container_path("D:\\", DRIVES) == PurePosixPath("/host/d")


@pytest.mark.parametrize("path", ["Projects\\Notes", "/etc", "W:relative", r"W:\a\..\b", "\\\\server\\share\\x", ""])
def test_relative_traversing_or_network_paths_are_rejected(path):
    with pytest.raises(InvalidHostPath):
        container_path(path, DRIVES)


def test_network_paths_say_why_they_are_refused():
    with pytest.raises(InvalidHostPath, match="only this PC's local drives"):
        container_path(r"\\nas\notes\project", DRIVES)
