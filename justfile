set shell := ["zsh", "-cu"]

default:
    just --list

build:
    @python builder.py