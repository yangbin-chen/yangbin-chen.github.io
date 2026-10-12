#!/usr/bin/env python3
"""Build students.html from content/ai-research-starter-guide.md.

Usage (from the project root):
    pip install markdown
    python3 scripts/build_students.py

Edit the Markdown file, re-run this script, and commit the regenerated
students.html. The page itself needs no build step to be served.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "content" / "ai-research-starter-guide.md"
OUTPUT = ROOT / "students.html"

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="AI 科研新手村 — a starter guide for students new to AI research, by Yangbin Chen (XJTLU)">
  <title>For Students — Yangbin Chen</title>
  <link rel="stylesheet" href="styles.css">
  <link rel="stylesheet" href="students.css">
</head>
<body>
  <header class="site-header">
    <nav class="top-nav" aria-label="Main">
      <a href="index.html" class="nav-brand">Yangbin Chen</a>
      <ul class="nav-links">
        <li><a href="index.html#about">About</a></li>
        <li><a href="index.html#research">Research</a></li>
        <li><a href="index.html#news">News</a></li>
        <li><a href="index.html#publications">Publications</a></li>
        <li><a href="students.html" class="active" aria-current="page">For Students</a></li>
        <li><a href="index.html#resume">Resume</a></li>
        <li><a href="index.html#motto">Motto</a></li>
        <li><a href="index.html#contact">Contact</a></li>
      </ul>
    </nav>
  </header>

  <div class="page-wrapper guide-wrapper">
    <aside class="guide-toc" aria-label="Guide contents">
      <p class="guide-toc-title">Contents · 目录</p>
      <ul>
{{TOC}}
      </ul>
    </aside>

    <main class="guide">
      <p class="guide-lead">
        <strong>For Students.</strong> A step-by-step starter guide for newcomers to AI research,
        prepared for incoming undergraduate and graduate students. The guide is written in Chinese;
        the linked courses, papers and tools are mostly in English.
      </p>
{{BODY}}
    </main>
  </div>

  <footer class="site-footer">
    <p>© 2026 Yangbin Chen · <a href="index.html">Homepage</a> · <a href="https://scholar.xjtlu.edu.cn/en/persons/YangbinChen/" target="_blank" rel="noopener">XJTLU Profile</a></p>
  </footer>

  <script type="module">
    import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
    mermaid.initialize({ startOnLoad: false, theme: "base", securityLevel: "strict" });
    mermaid.run({ querySelector: "pre.mermaid" });
  </script>
  <script>
    (function () {
      var links = Array.prototype.slice.call(document.querySelectorAll(".guide-toc a"));
      var byId = {};
      links.forEach(function (a) { byId[a.getAttribute("href").slice(1)] = a; });
      if (!("IntersectionObserver" in window)) return;
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting || !byId[entry.target.id]) return;
          links.forEach(function (a) { a.classList.remove("active"); });
          byId[entry.target.id].classList.add("active");
        });
      }, { rootMargin: "-15% 0px -75% 0px" });
      document.querySelectorAll(".guide h2[id]").forEach(function (h) { observer.observe(h); });
    })();
  </script>
</body>
</html>
"""

CALLOUT_LABELS = {"TIP": ("tip", "提示"), "NOTE": ("note", "注意")}


def preprocess(text: str) -> str:
    """Adapt the Markdown (written for Notion/GitHub readers) for the website."""
    # Notes that only make sense when importing the file into Notion/GitHub.
    text = re.sub(r"^> \*\*显示说明\*\*：.*\n\n?", "", text, flags=re.M)
    text = re.sub(r"；本文的色彩[^*\n]*。\*", "。*", text)
    # CommonMark ends a blockquote at a blank line; Python-Markdown would merge
    # neighbouring quotes. Split them so each callout stays a separate block.
    text = re.sub(r"(\n> [^\n]*)\n\n(?=> )", r"\1\n\n<!-- -->\n\n", text)
    # Put the explicit section anchors directly on the headings.
    text = re.sub(r'<a id="(section-\d+)"></a>\s*\n(#{2}) (.+)', r"\2 \3 {: #\1 }", text)
    # Python-Markdown merges blockquotes separated only by a blank line, whereas
    # GitHub keeps them separate. Keep them separate so each callout is its own box.
    text = re.sub(r"(?m)^(>.*)\n\n(?=>)", r"\1\n\n<!-- -->\n\n", text)
    # Let Markdown render inside <details> blocks (Toy Demos).
    return text.replace("<details>", '<details markdown="1">')


def postprocess(html: str) -> str:
    html = re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        r'<pre class="mermaid">\1</pre>',
        html,
        flags=re.S,
    )

    def callout(match: re.Match[str]) -> str:
        kind, label = CALLOUT_LABELS[match.group(1)]
        return (
            f'<blockquote class="callout callout-{kind}">\n'
            f'<p><span class="callout-label">{label}</span>'
        )

    html = re.sub(r"<blockquote>\s*<p>\[!(TIP|NOTE)\]\s*", callout, html)
    html = re.sub(r"<li>\[ \] ", '<li><input type="checkbox" disabled> ', html)
    html = re.sub(r"<li>\[[xX]\] ", '<li><input type="checkbox" checked disabled> ', html)
    html = re.sub(
        r'<a href="(https?://[^"]+)"',
        r'<a href="\1" target="_blank" rel="noopener"',
        html,
    )
    return html.replace("<table>", '<div class="table-wrap"><table>').replace(
        "</table>", "</table></div>"
    )


def build_toc(html: str) -> str:
    items = re.findall(r'<h2 id="(section-\d+)">(.*?)</h2>', html, flags=re.S)
    if not items:
        sys.exit("No section headings found; check the section anchors in the Markdown.")
    return "\n".join(
        f'        <li><a href="#{anchor}">{re.sub(r"<[^>]+>", "", title)}</a></li>'
        for anchor, title in items
    )


def main() -> None:
    source = preprocess(SOURCE.read_text(encoding="utf-8"))
    body = markdown.markdown(source, extensions=["extra", "sane_lists"])
    body = postprocess(body)
    page = TEMPLATE.replace("{{TOC}}", build_toc(body)).replace("{{BODY}}", body)
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
