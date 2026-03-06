"""
MkDocs hook: auto-generates docs/blog/index.md from post front matter.
Posts are sorted by date descending.
"""

from pathlib import Path
import yaml


def on_pre_build(config, **kwargs):
    docs_dir = Path(config["docs_dir"])
    posts_dir = docs_dir / "blog" / "posts"
    index_file = docs_dir / "blog" / "index.md"

    if not posts_dir.exists():
        return

    posts = []
    for md_file in sorted(posts_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        end = text.find("---", 3)
        if end == -1:
            continue
        front_matter = yaml.safe_load(text[3:end])
        posts.append(
            {
                "date": front_matter.get("date"),
                "title": front_matter.get("title", md_file.stem),
                "filename": md_file.name,
            }
        )

    posts.sort(key=lambda p: str(p["date"]), reverse=True)

    lines = [
        "# Blog\n",
        "\n",
        "| Date | Title |\n",
        "|---|---|\n",
    ]
    for post in posts:
        lines.append(
            f"| {post['date']} | [{post['title']}](posts/{post['filename']}) |\n"
        )

    index_file.write_text("".join(lines), encoding="utf-8")
