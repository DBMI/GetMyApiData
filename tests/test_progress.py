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

    # Test that setting the number of items to < 1 defaults to 1.
    progress.set(0)
    assert progress.is_set()
    assert progress.percent_complete() == 0
    progress.increment(1)
    assert progress.num_complete() == 1
    assert progress.percent_complete() == 100
