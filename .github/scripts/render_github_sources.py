#!/usr/bin/env python3
"""Render downloaded GitHub source snapshots into a compact markdown digest.

Used by the `update-github-info` agentic workflow. The agent runs inside the
gh-aw firewall sandbox without a web-fetch tool, so the workflow downloads the
source pages on the runner first and this script turns them into a digest the
agent can read from `/tmp/gh-aw/sources/github-sources.md`.

The downloads are untrusted network content, so parsing is deliberately
defensive: oversized payloads and documents carrying a DTD (the vector for
entity-expansion attacks against `xml.etree`) are rejected instead of parsed.
"""

from __future__ import annotations

import html
import os
import re
import sys
import xml.etree.ElementTree as ET

MAX_ITEMS = 15
MAX_SUMMARY_CHARS = 400
MAX_PAGE_CHARS = 4000
MAX_FILE_BYTES = 20 * 1024 * 1024

TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b.*?</\1>", re.IGNORECASE | re.DOTALL)
WHITESPACE_RE = re.compile(r"\s+")
DOCTYPE_RE = re.compile(r"<!\s*(DOCTYPE|ENTITY)\b", re.IGNORECASE)

ITEM_TAGS = ("item", "entry")


def plain_text(value):
    """Strip markup and collapse whitespace."""
    text = TAG_RE.sub(" ", value or "")
    return WHITESPACE_RE.sub(" ", html.unescape(text)).strip()


def truncate(value, limit):
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + "..."


def local_name(tag):
    """Return an element tag without its `{namespace}` prefix."""
    if isinstance(tag, str) and tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag if isinstance(tag, str) else ""


def read_source(path):
    """Read a snapshot file, or return None when it is unusable."""
    if not os.path.exists(path):
        return None, "Snapshot unavailable: this source could not be downloaded."
    if os.path.getsize(path) > MAX_FILE_BYTES:
        return None, "Snapshot rejected: downloaded file is unexpectedly large."
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read(), None


def child_text(item, *names):
    """Return the full text of the first matching child element."""
    wanted = set(names)
    for child in item:
        if local_name(child.tag) in wanted:
            text = "".join(child.itertext()).strip()
            if text:
                return text
            href = child.get("href")
            if href:
                return href
    return ""


def render_feed(path, heading, source_label, source_url):
    lines = ["## " + heading, "", "Source: %s (%s)" % (source_label, source_url), ""]

    markup, problem = read_source(path)
    if problem:
        lines += [problem, ""]
        return lines

    if DOCTYPE_RE.search(markup):
        lines += ["Snapshot rejected: feed declares a DTD and was not parsed.", ""]
        return lines

    try:
        root = ET.fromstring(markup)
    except Exception as error:  # noqa: BLE001 - untrusted input, never crash the step
        lines += ["Snapshot unreadable: %s" % error, ""]
        return lines

    items = [el for el in root.iter() if local_name(el.tag) in ITEM_TAGS][:MAX_ITEMS]
    if not items:
        lines += ["Snapshot contained no entries.", ""]
        return lines

    for item in items:
        title = plain_text(child_text(item, "title")) or "(untitled)"
        link = plain_text(child_text(item, "link", "id"))
        published = plain_text(child_text(item, "pubDate", "published", "updated"))
        summary = truncate(
            plain_text(child_text(item, "description", "summary", "encoded", "content")),
            MAX_SUMMARY_CHARS,
        )

        lines.append("### " + title)
        if published:
            lines.append("- Published: " + published)
        if link:
            lines.append("- Link: " + link)
        if summary:
            lines += ["", summary]
        lines.append("")

    return lines


def render_page(path, heading, source_label, source_url):
    lines = ["## " + heading, "", "Source: %s (%s)" % (source_label, source_url), ""]

    markup, problem = read_source(path)
    if problem:
        lines += [problem, ""]
        return lines

    text = truncate(plain_text(SCRIPT_STYLE_RE.sub(" ", markup)), MAX_PAGE_CHARS)
    lines += [text or "Snapshot contained no readable text.", ""]
    return lines


def main(argv):
    if len(argv) != 2:
        print("usage: %s <sources-dir>" % argv[0], file=sys.stderr)
        return 2

    sources_dir = argv[1]
    lines = [
        "# GitHub source snapshot",
        "",
        "Downloaded on the runner before the agent session started.",
        "",
    ]
    lines += render_feed(
        os.path.join(sources_dir, "github-blog.xml"),
        "GitHub Blog",
        "GitHub Blog",
        "https://github.blog/latest/",
    )
    lines += render_feed(
        os.path.join(sources_dir, "github-changelog.xml"),
        "GitHub Changelog",
        "GitHub Changelog",
        "https://github.blog/changelog/",
    )
    lines += render_page(
        os.path.join(sources_dir, "awesome-copilot-workflows.html"),
        "Awesome Copilot workflows",
        "Awesome Copilot",
        "https://awesome-copilot.github.com/workflows/",
    )

    digest = os.path.join(sources_dir, "github-sources.md")
    with open(digest, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines).rstrip() + "\n")

    print("wrote " + digest)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
