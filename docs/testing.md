# Testing

## Prerequisites

Activate the virtual environment and install pytest:

```bash
source .venv/bin/activate
uv pip install pytest
```

## Test Structure

Tests are in the `tests/` directory:

- **`test_cli.py`** — Unit tests for CLI argument parsing and input validation. Fast, no model downloads needed.
- **`test_integration.py`** — Integration tests that run actual upscaling. Slower, require network access on first run to download model weights.

## Running Tests

### Run all unit tests (fast)

```bash
pytest tests/test_cli.py -v
```

### Run all integration tests (slow, downloads models)

```bash
pytest tests/test_integration.py -v
```

### Run all tests

```bash
pytest -v
```

### Run only unit tests (skip integration)

```bash
pytest -v -m "not integration"
```

### Run only integration tests

```bash
pytest -v -m integration
```

### Run a specific test class or test

```bash
pytest tests/test_cli.py::TestScaleValidation -v
pytest tests/test_cli.py::TestScaleValidation::test_invalid_scale_3 -v
```

## Test Coverage

| Test File | What It Covers |
|-----------|---------------|
| `test_cli.py` | `--help` output, required args, `--scale` validation, `--model` validation, `--format` validation, input path existence check |
| `test_integration.py` | 4x upscale, 2x upscale, folder batch, format conversion, suffix option, face enhancement, error handling for corrupt files |
