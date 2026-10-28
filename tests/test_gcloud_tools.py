"""
Tests methods in class GCloudTools
"""

import pytest

from src.getmyapidata.gcloud_tools import (
    GCloudTools,
    getoutput,
    system,
)


def test_getoutput() -> None:
    # Exercise the 'command works' branch.
    try:
        result: list[str] = getoutput("dir")
        assert isinstance(result, list)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"'getoutput' raised an unexpected exception: {exc}")

    # Exercise the branch for when command doesn't work.
    try:
        result: list[str] = getoutput("ls")
        assert isinstance(result, list)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"'getoutput' raised an unexpected exception: {exc}")


@pytest.mark.skip(reason="No need to burn up token allotment.")
def test_instantiation(real_aou_package, logger) -> None:
    def on_auth_completion(progress: bool | int | str) -> None:
        if isinstance(progress, bool):
            logger.info("Authorization complete.")
        elif isinstance(progress, int):
            logger.info(f"progress: {progress}")
        elif isinstance(progress, str):
            logger.info(progress)

    gcloud_tools: GCloudTools = GCloudTools(
        aou_package=real_aou_package, log=logger, status_fn=on_auth_completion
    )
    assert isinstance(gcloud_tools, GCloudTools)
    gcloud_tools.start()

    # Wait until complete.
    gcloud_tools.join()

    token: str = gcloud_tools.get_token()
    assert isinstance(token, str)


def test_system() -> None:
    # Exercise the 'command works' branch.
    try:
        system("dir")
        assert True  # Add any other relevant assertions here
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"'system' raised an unexpected exception: {exc}")

    # Exercise the branch for when command doesn't work.
    try:
        system("ls")
        assert True  # Add any other relevant assertions here
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"'system' raised an unexpected exception: {exc}")
