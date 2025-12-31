"""Main module for opencode-testing."""

import logging
import sys
from typing import Any, Callable, Optional, Union

logger = logging.getLogger(__name__)


def hello(name: str = "World") -> str:
    """Return a greeting message.

    Args:
        name: Name to greet. Defaults to "World".

    Returns:
        Greeting message.
    """
    return f"Hello, {name}!"


def add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Add two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        Sum of a and b.
    """
    return a + b


def multiply(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Multiply two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        Product of a and b.
    """
    return a * b


def divide(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Divide two numbers.

    Args:
        a: Numerator.
        b: Denominator.

    Returns:
        Result of division.

    Raises:
        ValueError: If b is zero.
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def run(*args: Any, **kwargs: Any) -> int:
    """Main application entry point.

    Args:
        *args: Positional arguments.
        **kwargs: Keyword arguments.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    import argparse

    parser = argparse.ArgumentParser(description="opencode-testing application")
    parser.add_argument("--name", default="World", help="Name to greet")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--debug", action="store_true", help="Debug mode")

    parsed_args = parser.parse_args(args if args else sys.argv[1:])

    # Configure logging
    level = logging.DEBUG if parsed_args.debug else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        greeting = hello(parsed_args.name)
        print(greeting)

        # Example calculations
        print(f"2 + 3 = {add(2, 3)}")
        print(f"2 * 3 = {multiply(2, 3)}")
        print(f"6 / 3 = {divide(6, 3)}")

        return 0
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=parsed_args.debug)
        return 1


if __name__ == "__main__":
    sys.exit(run())