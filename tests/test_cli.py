"""Tests for CLI argument parsing and input validation (no model downloads needed)."""

import subprocess
import sys
from pathlib import Path

import pytest

PYTHON = sys.executable
SCRIPT = str(Path(__file__).resolve().parent.parent / "upscale.py")


def run_cli(*args):
    """Run upscale.py with the given args and return the CompletedProcess."""
    return subprocess.run(
        [PYTHON, SCRIPT, *args],
        capture_output=True,
        text=True,
    )


class TestHelpOutput:
    def test_help_exits_zero(self):
        result = run_cli("--help")
        assert result.returncode == 0

    def test_help_lists_all_arguments(self):
        result = run_cli("--help")
        for flag in [
            "--input", "--output", "--scale", "--model",
            "--face-enhance", "--tile", "--gpu-id", "--suffix", "--format",
        ]:
            assert flag in result.stdout, f"Missing {flag} in --help output"


class TestRequiredArgs:
    def test_missing_all_required_args(self):
        result = run_cli()
        assert result.returncode != 0
        assert "required" in result.stderr.lower()

    def test_missing_output(self):
        result = run_cli("-i", "some_file.png")
        assert result.returncode != 0

    def test_missing_input(self):
        result = run_cli("-o", "some_output.png")
        assert result.returncode != 0


class TestScaleValidation:
    def test_invalid_scale_3(self):
        result = run_cli("-i", "x", "-o", "y", "--scale", "3")
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower()

    def test_invalid_scale_8(self):
        result = run_cli("-i", "x", "-o", "y", "--scale", "8")
        assert result.returncode != 0

    def test_valid_scale_2(self):
        # Should not fail on scale validation (may fail on input path)
        result = run_cli("-i", "x", "-o", "y", "--scale", "2")
        assert "invalid choice" not in result.stderr.lower()

    def test_valid_scale_4(self):
        result = run_cli("-i", "x", "-o", "y", "--scale", "4")
        assert "invalid choice" not in result.stderr.lower()


class TestModelValidation:
    def test_invalid_model(self):
        result = run_cli("-i", "x", "-o", "y", "--model", "fantasy")
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower()

    def test_valid_model_general(self):
        result = run_cli("-i", "x", "-o", "y", "--model", "general")
        assert "invalid choice" not in result.stderr.lower()

    def test_valid_model_anime(self):
        result = run_cli("-i", "x", "-o", "y", "--model", "anime")
        assert "invalid choice" not in result.stderr.lower()


class TestFormatValidation:
    def test_invalid_format(self):
        result = run_cli("-i", "x", "-o", "y", "--format", "bmp")
        assert result.returncode != 0

    def test_valid_format_auto(self):
        result = run_cli("-i", "x", "-o", "y", "--format", "auto")
        assert "invalid choice" not in result.stderr.lower()


class TestInputPathValidation:
    def test_nonexistent_input_exits_with_error(self):
        result = run_cli("-i", "/tmp/nonexistent_upscaler_test.png", "-o", "/tmp/out.png")
        assert result.returncode != 0
        assert "does not exist" in result.stdout.lower()
