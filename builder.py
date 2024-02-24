import glob
import os
from pathlib import Path

import markdown

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
    ):
        html = markdown.markdown(source.read())
        dest.write(html)
