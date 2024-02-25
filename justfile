set shell := ["zsh", "-cu"]

default:
    just build

build:
    @python builder.py

generate-CSS:
    pygmentize -S default -f html -a .codehilite > pygmentize.css