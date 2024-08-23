set shell := ["zsh", "-cu"]

default:
    just --list

venv: 
  python -m venv .venv
  # Use uv package to pip install.
  # Ref: https://github.com/astral-sh/uv?tab=readme-ov-file#highlights
  export CONDA_PREFIX="" \
    && source .venv/bin/activate \
    && pip install --upgrade pip \
    && pip install uv \
    && uv pip install -r requirements.txt
  pre-commit install

build:
    @python src/builder.py

serve:
  just build
  python -m http.server
