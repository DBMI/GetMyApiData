from collections.abc import Callable as Callable

class GCloudTools:
    def __init__(
        self,
        pmi_account: str,
        project: str,
        aou_service_account: str,
        token_file: str,
        log_directory: str,
        status_fn: Callable = ...,
    ) -> None: ...
    def get_token(self) -> str: ...
