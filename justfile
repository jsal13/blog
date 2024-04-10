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

build:
    @python builder.py

# https://pygments.org/styles/
generate-CSS:
    pygmentize -S lightbulb -O linenos=1 -f html -a .codehilite > ./css/pygmentize.css
