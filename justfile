set shell := ["zsh", "-cu"]

default:
    just build

build:
    @python builder.py

# https://pygments.org/styles/
generate-CSS:
    pygmentize -S lightbulb -O linenos=1 -f html -a .codehilite > ./css/pygmentize.css
    