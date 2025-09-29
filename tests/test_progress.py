"""
Tests methods of Progress class.
"""
from src.getmyapidata.progress import Progress


def test_progress() -> None:
    progress = Progress()
    assert isinstance(progress, Progress)
    assert not progress.is_set()
    progress.set(10)
    assert progress.is_set()
    assert progress.percent_complete() == 0
    progress.increment(1)
    assert progress.num_complete() == 1
    assert progress.percent_complete() == 10
