"""Tests for CLI interface."""

import subprocess
import sys
import pytest
from click.testing import CliRunner
from opencode_testing.cli import main as cli_main


def test_cli_help():
    """Test CLI help command."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "opencode-testing" in result.output


def test_cli_version():
    """Test CLI version command."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()


def test_cli_run():
    """Test CLI run command."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["run", "--name", "Test"])
    assert result.exit_code == 0
    assert "Test" in result.output


def test_cli_subprocess():
    """Test CLI via subprocess."""
    result = subprocess.run(
        [sys.executable, "-m", "opencode_testing.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout


@pytest.mark.integration
def test_cli_integration():
    """Integration test for CLI."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["run", "--verbose"])
    assert result.exit_code == 0
    assert "running" in result.output.lower()