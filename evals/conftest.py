import pytest

from pi_runner import PiRunner


@pytest.fixture
def pi_runner():
    return PiRunner()
