import glob
import os
import re
from pathlib import Path

import attrs
import markdown

TEMPLATE_PATH = Path("src/template.html")
DEST_PATH = Path("html")

# Extensions for Markdown.
EXTENSIONS = ["fenced_code", "codehilite", "toc", "admonition"]
EXTENSION_CONFIGS = {"codehilite": {"linenums": True}}


@attrs.define()
class Post:
    """Represent Post object."""

    post_id: str
    title: Path
    source_path: Path
    dest_path: Path


class Converter:
    """Represent Converter Object."""

    def __init__(self, file_paths: list[str]):
        self.file_paths = file_paths
        self.post_info: list[Post] = []

    def convert_md_to_html(self, source_path: Path) -> None:
        """Convert a single markdown file into HTML."""
        # Convert MD files, add the metadata to ``self.post_info``.`
        source_path_obj: Path = Path(source_path)
        dest_path: Path = DEST_PATH.joinpath(Path(f"{source_path_obj.stem}.html"))

        with (
            source_path_obj.open(mode="r", encoding="utf-8") as source,
            dest_path.open(mode="w+", encoding="utf-8") as dest,
            TEMPLATE_PATH.open("r", encoding="utf-8") as template,
        ):
            # REF: https://python-markdown.github.io/extensions/code_hilite/#setup
            source_content: str = source.read()
            title: str = re.findall("^# (.*)", source_content)[0]
            # post_id = re.findall("<!-- ID: (\d+) -->", source_content)[0]
            post_id: str = source_path_obj.name
            html_body: str = markdown.markdown(
                source_content,
                extensions=EXTENSIONS,
                extension_configs=EXTENSION_CONFIGS,
            )
            str_replace_map: list[tuple[str, str]] = [
                (r"{{ content }}", html_body),
                (r"{{ title }}", title),
                (r"{{ title_matter }}", ""),
            ]

            html: str = template.read()
            for item in str_replace_map:
                html = html.replace(item[0], item[1])
            dest.write(html)

        # Add info to metadata if not a draft.
        file_name: str = source_path.split("/")[-1]
        if "__" not in file_name:  # If NOT a draft...
            post_obj = Post(
                post_id=post_id,
                title=title,
                source_path=source_path,
                dest_path=dest_path,
            )
            self.post_info.append(post_obj)

    def convert_all_md_to_html(self) -> None:
        """Convert all markdown files into HTML."""
        for file_path in self.file_paths:
            self.convert_md_to_html(source_path=file_path)

    def create_index_html(self) -> None:
        """Create index.html with ToC."""
        toc: list[str] = []

        # Sort posts by post_id value, smallest last.
        self.post_info.sort(key=lambda x: x.post_id, reverse=True)
        for post_obj in self.post_info:
            toc.append(f"<li><a href='{post_obj.dest_path}'>{post_obj.title}</a></li>")

        toc_str: str = "<ul>\n" + "\n".join(toc) + "\n</ul>"

        str_replace_map: list[tuple[str, str]] = [
            (r"{{ content }}", toc_str),
            (r"{{ title }}", "Blog"),
            (r"../css", r"./css"),
            (
                r"{{ title_matter }}",
                (
                    "<h1>jsalv neat things</h1>"
                    + "\n\n"
                    + "<p>Links & whatnot to things that seem pretty cool.</p>"
                ),
            ),
        ]

        with (
            TEMPLATE_PATH.open("r", encoding="utf-8") as template,
            Path("index.html").open("w+", encoding="utf-8") as dest,
        ):
            html: str = template.read()
            for item in str_replace_map:
                html = html.replace(item[0], item[1])

            dest.write(html)


if __name__ == "__main__":
    if not DEST_PATH.exists():
        os.makedirs(DEST_PATH)

    file_paths: list[str] = glob.glob("md/*.md")
    converter: Converter = Converter(file_paths=file_paths)
    converter.convert_all_md_to_html()
    converter.create_index_html()
