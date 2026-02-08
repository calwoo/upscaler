"""Integration tests that require model weights (downloaded on first run).

These tests are slower and require network access on the first run.
Mark with pytest marker 'integration' so they can be skipped easily.
"""

import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

PYTHON = sys.executable
SCRIPT = str(Path(__file__).resolve().parent.parent / "upscale.py")


def run_cli(*args):
    return subprocess.run(
        [PYTHON, SCRIPT, *args],
        capture_output=True,
        text=True,
        timeout=300,
    )


def make_test_image(path, width=64, height=64):
    """Create a small solid-color test image."""
    img = np.full((height, width, 3), (100, 150, 200), dtype=np.uint8)
    cv2.imwrite(str(path), img)


pytestmark = pytest.mark.integration


class TestSingleImage4x:
    """Test 2: Single image upscale (4x general)."""

    def test_output_exists_and_dimensions(self, tmp_path):
        input_img = tmp_path / "test.png"
        output_img = tmp_path / "output.png"
        make_test_image(input_img, 64, 64)

        result = run_cli("-i", str(input_img), "-o", str(output_img), "--scale", "4")
        assert (
            result.returncode == 0
        ), f"stderr: {result.stderr}\nstdout: {result.stdout}"
        assert output_img.exists(), "Output image was not created"

        img = cv2.imread(str(output_img))
        assert img.shape[1] == 256, f"Expected width 256, got {img.shape[1]}"
        assert img.shape[0] == 256, f"Expected height 256, got {img.shape[0]}"


class TestSingleImage2x:
    """Test 3: Single image upscale (2x general)."""

    def test_output_dimensions(self, tmp_path):
        input_img = tmp_path / "test.png"
        output_img = tmp_path / "output_2x.png"
        make_test_image(input_img, 64, 64)

        result = run_cli("-i", str(input_img), "-o", str(output_img), "--scale", "2")
        assert (
            result.returncode == 0
        ), f"stderr: {result.stderr}\nstdout: {result.stdout}"
        assert output_img.exists()

        img = cv2.imread(str(output_img))
        assert img.shape[1] == 128, f"Expected width 128, got {img.shape[1]}"
        assert img.shape[0] == 128, f"Expected height 128, got {img.shape[0]}"


class TestFolderBatch:
    """Test 4: Folder batch processing."""

    def test_all_images_upscaled(self, tmp_path):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        for name in ["a.png", "b.jpg", "c.png"]:
            make_test_image(input_dir / name, 32, 32)

        result = run_cli("-i", str(input_dir), "-o", str(output_dir), "--scale", "4")
        assert (
            result.returncode == 0
        ), f"stderr: {result.stderr}\nstdout: {result.stdout}"
        assert output_dir.exists()

        output_files = sorted(f.name for f in output_dir.iterdir())
        assert len(output_files) == 3, f"Expected 3 output files, got {output_files}"


class TestOutputFormat:
    """Test 5: Output format conversion."""

    def test_png_to_jpg(self, tmp_path):
        input_img = tmp_path / "test.png"
        output_img = tmp_path / "output.jpg"
        make_test_image(input_img, 32, 32)

        result = run_cli(
            "-i",
            str(input_img),
            "-o",
            str(output_img),
            "--scale",
            "4",
            "--format",
            "jpg",
        )
        assert (
            result.returncode == 0
        ), f"stderr: {result.stderr}\nstdout: {result.stdout}"
        # Check that a .jpg file was created
        jpg_files = list(tmp_path.glob("*.jpg"))
        assert len(jpg_files) >= 1, "No .jpg output file found"


class TestSuffix:
    """Test 6: Suffix option."""

    def test_custom_suffix_in_folder_mode(self, tmp_path):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        make_test_image(input_dir / "photo.png", 32, 32)

        result = run_cli(
            "-i",
            str(input_dir),
            "-o",
            str(output_dir),
            "--scale",
            "4",
            "--suffix",
            "_4x",
        )
        assert (
            result.returncode == 0
        ), f"stderr: {result.stderr}\nstdout: {result.stdout}"
        output_files = list(output_dir.iterdir())
        assert any(
            "_4x" in f.name for f in output_files
        ), f"No file with '_4x' suffix found: {[f.name for f in output_files]}"


class TestFaceEnhancement:
    """Test 7: Face enhancement."""

    def test_face_enhance_runs(self, tmp_path):
        input_img = tmp_path / "face.png"
        output_img = tmp_path / "face_out.png"
        make_test_image(input_img, 64, 64)

        result = run_cli(
            "-i",
            str(input_img),
            "-o",
            str(output_img),
            "--scale",
            "4",
            "--face-enhance",
        )
        assert (
            result.returncode == 0
        ), f"stderr: {result.stderr}\nstdout: {result.stdout}"
        assert output_img.exists()


class TestErrorHandling:
    """Test 8: Error handling."""

    def test_nonexistent_input(self):
        result = run_cli("-i", "/tmp/does_not_exist_upscaler.png", "-o", "/tmp/out.png")
        assert result.returncode != 0

    def test_corrupt_file_in_batch(self, tmp_path):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        make_test_image(input_dir / "good.png", 32, 32)
        (input_dir / "bad.png").write_text("this is not an image")

        result = run_cli("-i", str(input_dir), "-o", str(output_dir), "--scale", "4")
        # Should not crash — exits 0 and processes the good image
        assert (
            result.returncode == 0
        ), f"stderr: {result.stderr}\nstdout: {result.stdout}"
        assert (output_dir / "good_upscaled.png").exists() or len(
            list(output_dir.iterdir())
        ) >= 1
