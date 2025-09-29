"""
Tests methods in class GCloudTools
"""
import pytest

from src.getmyapidata.gcloud_tools import GCloudTools


@pytest.mark.skip(reason="No need to burn up token allotment.")
def test_instantiation(fake_aou_package, fake_logger) -> None:
    gcloud_tools: GCloudTools = GCloudTools(
        aou_package=fake_aou_package, log=fake_logger
    )
    assert isinstance(gcloud_tools, GCloudTools)
    token: str = gcloud_tools.get_token()
    assert isinstance(token, str)
