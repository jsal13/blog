from dataclasses import dataclass
import glob
import os
from pathlib import Path
import re

import markdown

TEMPLATE_PATH = Path("template.html")
DEST_PATH = Path("html")

# Extensions for Markdown.
EXTENSIONS = ["fenced_code", "codehilite", "toc"]
EXTENSION_CONFIGS = {"toc": {"permalink": True}, "codehilite": {"linenums": True}}


@dataclass
class Post:
    _id: str
    title: Path
    source_path: Path
    dest_path: Path


class Converter:

    def __init__(self, file_paths: list[str]):
        self.file_paths = file_paths
        self.post_info: list[Post] = []

    def convert_md_to_html(self, source_path: Path) -> None:
        # Convert MD files, add the metadata to ``self.post_info``.`
        source_path_obj = Path(source_path)
        dest_path = DEST_PATH.joinpath(Path(f"{source_path_obj.stem}.html"))

        with (
            source_path_obj.open(mode="r", encoding="utf-8") as source,
            dest_path.open(mode="w+", encoding="utf-8") as dest,
            TEMPLATE_PATH.open("r", encoding="utf-8") as template,
        ):
            # REF: https://python-markdown.github.io/extensions/code_hilite/#setup
            source_content = source.read()
            title = re.findall("^# (.*)", source_content)[0]
            _id = re.findall("<!-- ID: (\d+) -->", source_content)[0]
            html_body = markdown.markdown(
                source_content,
                extensions=EXTENSIONS,
                extension_configs=EXTENSION_CONFIGS,
            )

            html = (
                template.read()
                .replace(r"{{ content }}", html_body)
                .replace(r"{{ title }}", title)
                .replace(r"{{ title_matter }}", "")
            )
            dest.write(html)

        # Add info to metadata if not a draft.
        file_name = source_path.split("/")[-1]
        if file_name[0] != "_":  # If NOT a draft...
            post_obj = Post(
                _id=_id, title=title, source_path=source_path, dest_path=dest_path
            )
            self.post_info.append(post_obj)

    def convert_all_md_to_html(self) -> None:
        for file_path in self.file_paths:
            self.convert_md_to_html(source_path=file_path)

    def create_index_html(self) -> None:
        """Create index.html with ToC."""
        toc = []

        # Sort posts by _id value, smallest last.
        self.post_info.sort(key=lambda x: x._id, reverse=True)

        for post_obj in self.post_info:
            toc.append(f"<li><a href='{post_obj.dest_path}'>{post_obj.title}</a></li>")

        toc_str = "<ul>\n" + "\n".join(toc) + "\n</ul>"

        with (
            TEMPLATE_PATH.open("r", encoding="utf-8") as template,
            Path("index.html").open("w+", encoding="utf-8") as dest,
        ):
            html = (
                template.read()
                .replace(r"{{ content }}", toc_str)
                .replace(r"{{ title }}", "Blog")
                .replace(r"{{ title_matter }}", "<h1>JSalv Blog Posts</h1>")
            )
            dest.write(html)


if __name__ == "__main__":
    if not DEST_PATH.exists():
        os.makedirs(DEST_PATH)

    file_paths = glob.glob("md/*.md")
    converter = Converter(file_paths=file_paths)
    converter.convert_all_md_to_html()
    converter.create_index_html()
