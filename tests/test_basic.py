"""Basic tests for opencode-testing."""

import pytest
from opencode_testing import __version__
from opencode_testing.main import hello, add


def test_version():
    """Test that version is defined."""
    assert __version__ == "0.1.0"


def test_hello():
    """Test hello function."""
    result = hello("World")
    assert result == "Hello, World!"


def test_add():
    """Test add function."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_add_with_negative():
    """Test add function with negative numbers."""
    assert add(-5, -3) == -8


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (1, 2, 3),
        (0, 0, 0),
        (-1, 1, 0),
        (100, 200, 300),
    ],
)
def test_add_parametrized(a, b, expected):
    """Test add function with multiple parameters."""
    assert add(a, b) == expected


@pytest.mark.slow
def test_slow_operation():
    """Example of a slow test that can be skipped."""
    import time

    time.sleep(0.1)  # Simulate slow operation
    assert True


class TestMathOperations:
    """Test class for math operations."""

    def test_multiply(self):
        """Test multiplication operation."""
        from opencode_testing.main import multiply

        assert multiply(2, 3) == 6
        assert multiply(0, 5) == 0
        assert multiply(-2, 3) == -6

    def test_divide(self):
        """Test division operation."""
        from opencode_testing.main import divide

        assert divide(6, 3) == 2
        assert divide(0, 5) == 0

        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(5, 0)


def test_fixture_example(tmpdir):
    """Example test using pytest fixtures."""
    temp_file = tmpdir.join("test.txt")
    temp_file.write("content")
    assert temp_file.read() == "content"