"""
Tests methods in class GCloudTools
"""

import os
import subprocess

from src.getmyapidata.gcloud_tools import (
    gcloud_tools_installed,
)


def windows_test_installed() -> None:
    assert gcloud_tools_installed()

    # Temporarily rename gcloud.cmd to exercise code that handles the not-installed condition.
    file_path: str = subprocess.check_output(
        "where gcloud.cmd", shell=True, stderr=subprocess.STDOUT, text=True
    ).strip()
    directory: str = os.path.dirname(file_path)
    just_the_filename: str = os.path.basename(file_path).strip()
    full_new_file_path: str = os.path.join(directory, "renamed_" + just_the_filename)
    os.rename(file_path, full_new_file_path)
    assert not gcloud_tools_installed()

    # Restore to original name.
    os.rename(full_new_file_path, file_path)


if __name__ == "__main__":
    windows_test_installed()
