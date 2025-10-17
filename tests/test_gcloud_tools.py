"""
Tests methods in class GCloudTools
"""
import os
import subprocess
from typing import Union

import pytest

from src.getmyapidata.gcloud_tools import (GCloudTools, gcloud_tools_installed,
                                           getoutput, system)


def test_getoutput() -> None:
    # Exercise the 'command works' branch.
    try:
        result: list[str] = getoutput("dir")
        assert isinstance(result, list)
    except Exception as exc:
        pytest.fail(f"'getoutput' raised an unexpected exception: {exc}")

    # Exercise the branch for when command doesn't work.
    try:
        result: list[str] = getoutput("ls")
        assert isinstance(result, list)
    except Exception as exc:
        pytest.fail(f"'getoutput' raised an unexpected exception: {exc}")


@pytest.mark.skip(reason="No need to burn up token allotment.")
def test_instantiation(real_aou_package, fake_logger) -> None:
    def on_auth_completion(progress: Union[bool, int, str]) -> None:
        if isinstance(progress, bool):
            fake_logger.info("Authorization complete.")
        elif isinstance(progress, int):
            fake_logger.info(f"progress: {progress}")
        elif isinstance(progress, str):
            fake_logger.info(progress)

    gcloud_tools: GCloudTools = GCloudTools(
        aou_package=real_aou_package, log=fake_logger, status_fn=on_auth_completion
    )
    assert isinstance(gcloud_tools, GCloudTools)
    gcloud_tools.start()

    # Wait until complete.
    gcloud_tools.join()

    token: str = gcloud_tools.get_token()
    assert isinstance(token, str)


def test_installed() -> None:
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


def test_system() -> None:
    # Exercise the 'command works' branch.
    try:
        system("dir")
        assert True  # Add any other relevant assertions here
    except Exception as exc:
        pytest.fail(f"'system' raised an unexpected exception: {exc}")

    # Exercise the branch for when command doesn't work.
    try:
        system("ls")
        assert True  # Add any other relevant assertions here
    except Exception as exc:
        pytest.fail(f"'system' raised an unexpected exception: {exc}")
