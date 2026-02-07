"""Tests for input/output path resolution logic (no model downloads needed)."""

import sys
from argparse import Namespace
from pathlib import Path

import cv2
import numpy as np
import pytest

# Add project root to path so we can import resolve_paths directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from upscale import resolve_paths, IMAGE_EXTENSIONS


def make_test_image(path, width=32, height=32):
    img = np.full((height, width, 3), (100, 150, 200), dtype=np.uint8)
    cv2.imwrite(str(path), img)


def make_args(**overrides):
    defaults = {
        "input": "/tmp",
        "output": "/tmp/out",
        "scale": 4,
        "model": "general",
        "face_enhance": False,
        "tile": 0,
        "gpu_id": None,
        "suffix": "_upscaled",
        "format": "auto",
    }
    defaults.update(overrides)
    return Namespace(**defaults)


class TestSingleFileMode:
    def test_single_file_returns_one_pair(self, tmp_path):
        img = tmp_path / "photo.png"
        make_test_image(img)
        out = tmp_path / "result.png"

        args = make_args(input=str(img), output=str(out))
        pairs = resolve_paths(args)

        assert len(pairs) == 1
        assert pairs[0][0] == img
        assert pairs[0][1] == out

    def test_single_file_creates_parent_dirs(self, tmp_path):
        img = tmp_path / "photo.png"
        make_test_image(img)
        out = tmp_path / "sub" / "dir" / "result.png"

        args = make_args(input=str(img), output=str(out))
        resolve_paths(args)

        assert out.parent.exists()

    def test_single_file_format_override(self, tmp_path):
        img = tmp_path / "photo.png"
        make_test_image(img)
        out = tmp_path / "result.png"

        args = make_args(input=str(img), output=str(out), format="jpg")
        pairs = resolve_paths(args)

        assert pairs[0][1].suffix == ".jpg"


class TestDirectoryMode:
    def test_collects_all_image_files(self, tmp_path):
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        for name in ["a.png", "b.jpg", "c.jpeg", "d.webp", "e.bmp"]:
            make_test_image(input_dir / name)

        args = make_args(input=str(input_dir), output=str(tmp_path / "out"))
        pairs = resolve_paths(args)

        assert len(pairs) == 5

    def test_ignores_non_image_files(self, tmp_path):
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        make_test_image(input_dir / "photo.png")
        (input_dir / "readme.txt").write_text("not an image")
        (input_dir / "data.json").write_text("{}")

        args = make_args(input=str(input_dir), output=str(tmp_path / "out"))
        pairs = resolve_paths(args)

        assert len(pairs) == 1

    def test_creates_output_directory(self, tmp_path):
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        make_test_image(input_dir / "photo.png")
        output_dir = tmp_path / "new_output"

        args = make_args(input=str(input_dir), output=str(output_dir))
        resolve_paths(args)

        assert output_dir.exists()

    def test_applies_suffix(self, tmp_path):
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        make_test_image(input_dir / "photo.png")

        args = make_args(
            input=str(input_dir),
            output=str(tmp_path / "out"),
            suffix="_4x",
        )
        pairs = resolve_paths(args)

        assert pairs[0][1].stem == "photo_4x"

    def test_applies_format_override(self, tmp_path):
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        make_test_image(input_dir / "photo.png")

        args = make_args(
            input=str(input_dir),
            output=str(tmp_path / "out"),
            format="jpg",
        )
        pairs = resolve_paths(args)

        assert pairs[0][1].suffix == ".jpg"

    def test_auto_format_preserves_extension(self, tmp_path):
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        make_test_image(input_dir / "photo.png")

        args = make_args(
            input=str(input_dir),
            output=str(tmp_path / "out"),
            format="auto",
        )
        pairs = resolve_paths(args)

        assert pairs[0][1].suffix == ".png"

    def test_empty_directory_returns_no_pairs(self, tmp_path):
        input_dir = tmp_path / "empty"
        input_dir.mkdir()

        args = make_args(input=str(input_dir), output=str(tmp_path / "out"))
        pairs = resolve_paths(args)

        assert len(pairs) == 0

    def test_output_paths_are_sorted(self, tmp_path):
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        for name in ["c.png", "a.png", "b.png"]:
            make_test_image(input_dir / name)

        args = make_args(input=str(input_dir), output=str(tmp_path / "out"))
        pairs = resolve_paths(args)

        stems = [p[0].stem for p in pairs]
        assert stems == ["a", "b", "c"]
