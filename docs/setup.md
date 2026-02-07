# Setup

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)

## Create Virtual Environment

```bash
cd /home/calvin/projects/upscaler
uv venv
source .venv/bin/activate
```

This creates a `.venv/` directory using CPython 3.12.3. The directory is excluded from git via `.gitignore`.

## Install Dependencies

```bash
uv pip install -r requirements.txt
```
