import glob
import os
from pathlib import Path
import shutil

import markdown

TEMPLATE_PATH = Path("template.html")
DEST_PATH = Path("_build")
if not DEST_PATH.exists():
    os.makedirs(DEST_PATH)

file_paths = glob.glob("posts/*.md")


for file_path in file_paths:
    source_path = Path(file_path)
    dest_path = DEST_PATH.joinpath(Path(f"{source_path.stem}.html"))

    with (
        source_path.open(mode="r", encoding="utf-8") as source,
        dest_path.open(mode="w+", encoding="utf-8") as dest,
        TEMPLATE_PATH.open("r", encoding="utf-8") as template,
    ):
        # REF: https://python-markdown.github.io/extensions/code_hilite/#setup
        html_body = markdown.markdown(
            source.read(), extensions=["fenced_code", "codehilite"]
        )
        html = template.read().replace(r"{{ content }}", html_body)
        dest.write(html)

shutil.copy("styles.css", DEST_PATH)
