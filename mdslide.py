#!/usr/bin/env python3
"""mdslide - turn a Markdown outline into a self-contained HTML slide deck.

Pure Python standard library. No dependencies, no build step, fully offline.

Features:
  * Split slides on ``---`` horizontal rules or on headings (``--split headings``)
  * Presenter notes via HTML comments (``<!-- note: ... -->``)
  * Keyboard navigation, progress bar, fullscreen
  * Presenter drawer with speaker notes + run timer (P / T / R)
  * Dark mode toggle that respects prefers-color-scheme, persisted locally
  * Print-to-PDF friendly CSS with large-type output
  * Built-in themes plus your own CSS overrides (--theme, --css)
  * Accessibility checks: text contrast ratios (WCAG) and missing image alt text
  * Export speaker notes to a Markdown file (--export-notes)

Copyright (c) 2026 Asdale Dynamics, LLC
Released under the MIT License.
"""

from __future__ import annotations

import argparse
import html
import re
import string
import sys
from pathlib import Path

__version__ = "1.0.0"
__author__ = "Asdale Dynamics, LLC"

# ---------------------------------------------------------------------------
# Themes
# ---------------------------------------------------------------------------

THEMES = {
    "default": {
        "name": "Default (warm paper)",
        "light": {
            "bg": "#fdf8f2", "fg": "#2b2523", "muted": "#5f5551",
            "accent": "#8a4b12", "link": "#1d5d90", "head": "#3d2f28",
            "code_bg": "#f3e9dc", "border": "#e0d3c4", "mark": "#fff3bf",
        },
        "dark": {
            "bg": "#201916", "fg": "#f3ece4", "muted": "#c9beb4",
            "accent": "#f0b064", "link": "#8ec3ee", "head": "#ffe6cf",
            "code_bg": "#332a24", "border": "#4a3e35", "mark": "#6b5a1e",
        },
    },
    "forest": {
        "name": "Forest (calm green)",
        "light": {
            "bg": "#f4f8f3", "fg": "#22301f", "muted": "#42503e",
            "accent": "#2f6b3a", "link": "#255a8a", "head": "#1d4426",
            "code_bg": "#e2ede0", "border": "#ccdcc9", "mark": "#e4f2c8",
        },
        "dark": {
            "bg": "#16211a", "fg": "#e7f0e4", "muted": "#aebfa9",
            "accent": "#7fd493", "link": "#8fc4ea", "head": "#c4e8cd",
            "code_bg": "#233128", "border": "#33453a", "mark": "#54622a",
        },
    },
    "midnight": {
        "name": "Midnight (always dark)",
        "light": {
            "bg": "#12151d", "fg": "#e9ecf1", "muted": "#a5aebc",
            "accent": "#7aa7ff", "link": "#7ac8ff", "head": "#d7deea",
            "code_bg": "#1e2330", "border": "#2c3342", "mark": "#3a4a63",
        },
        "dark": {
            "bg": "#0c0e14", "fg": "#eef1f6", "muted": "#a8b1bf",
            "accent": "#82adff", "link": "#7fd0ff", "head": "#dde4ef",
            "code_bg": "#181d29", "border": "#262d3c", "mark": "#33415c",
        },
    },
    "high-contrast": {
        "name": "High contrast (black on white)",
        "light": {
            "bg": "#ffffff", "fg": "#000000", "muted": "#000000",
            "accent": "#003b8e", "link": "#003b8e", "head": "#000000",
            "code_bg": "#f0f0f0", "border": "#000000", "mark": "#ffff99",
        },
        "dark": {
            "bg": "#000000", "fg": "#ffffff", "muted": "#ffffff",
            "accent": "#7fc8ff", "link": "#7fc8ff", "head": "#ffffff",
            "code_bg": "#1a1a1a", "border": "#ffffff", "mark": "#3d3d00",
        },
    },
    "large-print": {
        "name": "Large print (big, roomy type)",
        "light": {
            "bg": "#ffffff", "fg": "#111111", "muted": "#222222",
            "accent": "#8a1c1c", "link": "#0b4f9c", "head": "#000000",
            "code_bg": "#f2f2f2", "border": "#8f8f8f", "mark": "#ffef8f",
        },
        "dark": {
            "bg": "#101010", "fg": "#ffffff", "muted": "#e6e6e6",
            "accent": "#ffab90", "link": "#9ecbff", "head": "#ffffff",
            "code_bg": "#232323", "border": "#d5d5d5", "mark": "#574d00",
        },
    },
}

# palette keys used as (foreground, description) against the background
TEXT_PAIRS = [("fg", "Body text"), ("muted", "Secondary text"),
              ("link", "Links"), ("accent", "Accents")]

# ---------------------------------------------------------------------------
# Markdown parsing (small, deliberate subset)
# ---------------------------------------------------------------------------


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def slugify(text: str, seen: set) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "slide"
    slug, n = base, 1
    while slug in seen:
        n += 1
        slug = f"{base}-{n}"
    seen.add(slug)
    return slug


def inline(text: str) -> str:
    """Inline markdown: code spans, images, links, bold, emphasis,
    strikethrough and autolinks. Raw HTML is escaped (output stays safe)."""
    text = esc(text)
    placeholders: list[str] = []

    def code_sub(m):
        placeholders.append(f"<code>{m.group(2).strip()}</code>")
        return f"\x00md{len(placeholders) - 1}\x00"

    text = re.sub(r"(`+)([^`]+)\1", code_sub, text)

    def img_sub(m):
        alt, src = m.group(1).strip(), m.group(2)
        return f'<img src="{src}" alt="{alt}" loading="lazy">'

    text = re.sub(
        r'!\[([^\]]*)\]\(\s*([^)\s]+)\s*(?:&quot;[^)]*&quot;|"[^)]*")?\)',
        img_sub, text)

    def link_sub(m):
        return f'<a href="{m.group(2)}">{m.group(1)}</a>'

    text = re.sub(r"\[([^\]]+)\]\(\s*([^)\s]+)\s*\)", link_sub, text)

    text = re.sub(r"&lt;(https?://[^&>\s]+)&gt;",
                  lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', text)

    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\s][^*]*?)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"(?<![\w])_([^_\s][^_]*?)_(?![\w])", r"<em>\1</em>", text)
    text = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", text)

    def put(m):
        return placeholders[int(m.group(1))]

    text = re.sub(r"\x00md(\d+)\x00", put, text)
    return text


def _fence_marker(line: str):
    """Return (marker, lang) for a fence line, or None."""
    m = re.match(r"^\s{0,3}(`{3,}|~{3,})\s*([^`]*)\s*$", line)
    if not m:
        return None
    return m.group(1), m.group(2).strip()


def parse_fences(lines):
    """Split lines into ("line", None, text) and ("fence", lang, [code])
    tokens, so fenced code is never parsed as markdown."""
    out: list[tuple] = []
    fence: str | None = None
    lang = ""
    buf: list[str] = []
    for line in lines:
        marker = _fence_marker(line)
        if fence is None and marker is not None:
            fence, lang, buf = marker[0], marker[1], []
            continue
        if fence is not None and set(line.strip()) <= {fence[0]} \
                and line.strip():
            out.append(("fence", lang, buf))
            fence, lang, buf = None, "", []
            continue
        if fence is not None:
            buf.append(line)
        else:
            out.append(("line", None, line))
    if fence is not None:
        out.append(("fence", lang, buf))
    return out


def parse_blocks(lines):
    """Markdown block-level parsing. Supports headings, paragraphs, lists
    (with nesting), blockquotes, GFM tables, fenced code and rules."""
    groups = parse_fences(lines)
    out_html: list[str] = []
    i = 0
    n = len(groups)
    while i < n:
        kind, lang, payload = groups[i]
        if kind == "fence":
            code = esc("".join(payload)).rstrip("\n")
            cls = f' class="lang-{esc(lang)}"' if lang else ""
            out_html.append(f"<pre><code{cls}>{code}\n</code></pre>")
            i += 1
            continue

        line = payload.rstrip("\n")
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Heading
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            level = len(m.group(1))
            out_html.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^(\*\s*\*\s*\*[\s*]*|\-\s*\-\s*\-[\s-]*|_\s*_\s*_[\s_]*)$",
                    stripped):
            out_html.append("<hr>")
            i += 1
            continue

        # Table (GFM simple)
        if (stripped.startswith("|") and i + 1 < n
                and groups[i + 1][0] == "line" and re.match(
                    r"^\|?[\s:\-|]+\|[\s:\-|]*$",
                    groups[i + 1][2].strip())):
            head_cells = [c.strip() for c in stripped.strip("|").split("|")]
            raw_aligns = [a.strip() for a in
                          groups[i + 1][2].strip().strip("|").split("|")]
            align = []
            for a in raw_aligns:
                if a.startswith(":") and a.endswith(":"):
                    align.append("center")
                elif a.endswith(":"):
                    align.append("right")
                else:
                    align.append("left")
            i += 2
            rows = []
            while (i < n and groups[i][0] == "line"
                   and groups[i][2].strip().startswith("|")):
                rows.append([c.strip() for c in
                             groups[i][2].strip().strip("|").split("|")])
                i += 1
            t = ["<table><thead><tr>"]
            for ci, col in enumerate(head_cells):
                al = align[ci] if ci < len(align) else "left"
                t.append(f'<th style="text-align:{al}">{inline(col)}</th>')
            t.append("</tr></thead><tbody>")
            for row in rows:
                t.append("<tr>")
                for ci, cell in enumerate(row):
                    al = align[ci] if ci < len(align) else "left"
                    t.append(f'<td style="text-align:{al}">{inline(cell)}</td>')
                t.append("</tr>")
            t.append("</tbody></table>")
            out_html.append("".join(t))
            continue

        # Blockquote
        if stripped.startswith(">"):
            quote = [stripped.lstrip("> ").strip()]
            i += 1
            while (i < n and groups[i][0] == "line"
                   and groups[i][2].strip().startswith(">")):
                quote.append(groups[i][2].strip().lstrip("> ").strip())
                i += 1
            quote = [q for q in quote if q]
            body = "<br>".join(inline(q) for q in quote) or " "
            out_html.append(f"<blockquote>{body}</blockquote>")
            continue

        # List
        if re.match(r"^(\s*)([-*+]|\d+[.)])\s+", line):
            rendered, i = collect_list(groups, i)
            out_html.append(rendered)
            continue

        # Paragraph
        para = [stripped]
        i += 1
        while (i < n and groups[i][0] == "line"):
            nxt = groups[i][2].strip()
            if (not nxt or re.match(r"^(#{1,6})\s+", nxt) or nxt.startswith(">")
                    or nxt.startswith("|")
                    or re.match(r"^([-*+]|\d+[.)])\s+", nxt)
                    or re.match(r"^(\*\s*\*\s*\*[\s*]*|\-\s*\-\s*\-[\s-]*"
                                r"|_\s*_\s*_[\s_]*)$", nxt)):
                break
            para.append(nxt)
            i += 1
        out_html.append(f"<p>{'<br>'.join(inline(p) for p in para)}</p>")

    return "\n".join(out_html)


def collect_list(groups, i):
    """Collect consecutive list items with simple nesting (any depth).

    Returns (html, next_index)."""
    entries: list[tuple[int, bool, list[str]]] = []
    n = len(groups)

    def is_item(s: str):
        return re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", s)

    while i < n:
        kind, _, payload = groups[i]
        if kind != "line":
            if kind == "fence":
                break
            i += 1
            continue
        raw = payload.rstrip("\n")
        if not raw.strip():
            j = i + 1
            while (j < n and groups[j][0] == "line"
                   and not groups[j][2].strip()):
                j += 1
            if j < n and groups[j][0] == "line" and is_item(groups[j][2]):
                i = j
                continue
            i += 1
            break
        m = is_item(raw)
        if not m:
            if entries and raw.startswith(" ") and raw.strip():
                # indented continuation of the previous list item
                entries[-1][2].append(raw.strip())
                i += 1
                continue
            break
        indent = len(m.group(1).expandtabs(4))
        ordered = m.group(2)[0].isdigit()
        entries.append((indent, ordered, [m.group(3).strip()]))
        i += 1

    if not entries:
        return "", i

    def build(start, indent):
        parts = []
        while start < len(entries):
            ind, ordered, texts = entries[start]
            if ind < indent:
                break
            # a sibling run shares indent and list type; a marker-type
            # change (ul vs ol) at the same indent starts a new list
            tag = "ol" if ordered else "ul"
            run = []
            run_start = start
            while (start < len(entries)
                   and entries[start][0] == ind
                   and entries[start][1] == ordered):
                start += 1
            for k in range(run_start, start):
                nested, sub = build(k + 1, ind + 1)
                start = max(start, sub)
                body = inline("<br>".join(entries[k][2]))
                if nested:
                    # build() returns fully wrapped <ul>/<ol> lists
                    run.append(f"<li>{body}\n{''.join(nested)}</li>")
                else:
                    run.append(f"<li>{body}</li>")
            parts.append(f"<{tag}>{''.join(run)}</{tag}>")
        return parts, start

    parts, _ = build(0, entries[0][0])
    return "".join(parts), i


# ---------------------------------------------------------------------------
# Slides
# ---------------------------------------------------------------------------


class Slide:
    def __init__(self, lines, seen_slugs: set):
        self.lines = [ln for ln in lines]
        body, notes = self._split_notes()
        self.body_lines = body
        self.notes = notes
        self.title = "(slide)"
        for line in self.body_lines:
            m = re.match(r"^#{1,3}\s+(.*)$", line.strip())
            if m:
                self.title = m.group(1).strip()
                break
        self.slug = slugify(self.title, seen_slugs)

    def _split_notes(self):
        text = "\n".join(self.lines)
        notes: list[str] = []

        def grab(m):
            inner = m.group(1).strip()
            inner = re.sub(r"^-+\s*notes?:\s*", "", inner,
                           flags=re.I | re.DOTALL).strip()
            inner = re.sub(r"^notes?:\s*", "", inner, flags=re.I).strip()
            if inner:
                notes.append(inner)
            return ""

        text = re.sub(r"<!\-\-(.*?)\-\->", grab, text, flags=re.S)
        body = text.split("\n")
        return body, "\n\n".join(n for n in notes if n)

    def content_html(self) -> str:
        return parse_blocks(self.body_lines)

    @property
    def notes_markdown(self) -> str:
        return self.notes.strip()

    @property
    def is_title_slide(self) -> bool:
        return any(re.match(r"^#\s+", ln.strip()) for ln in self.body_lines)


def split_slides(markdown_text: str, mode: str = "hr",
                 heading_level: int = 2, title: str | None = None):
    lines = markdown_text.replace("\r\n", "\n").split("\n")
    slides: list[Slide] = []
    current: list[str] = []
    seen: set = set()

    def flush():
        if any(ln.strip() for ln in current):
            slides.append(Slide(current, seen))
            current.clear()

    in_fence = False
    if mode == "hr":
        for line in lines:
            marker = _fence_marker(line)
            if fence_live(in_fence, marker, line):
                in_fence = False
            elif not in_fence and marker is not None:
                in_fence = True
            if not in_fence and re.match(r"^\s{0,3}(---+|\*\*\*+|___+)\s*$",
                                         line):
                flush()
                continue
            current.append(line)
        flush()
    else:
        for line in lines:
            marker = _fence_marker(line)
            if fence_live(in_fence, marker, line):
                in_fence = False
            elif not in_fence and marker is not None:
                in_fence = True
            if not in_fence:
                m = re.match(r"^(#{1,6})\s+", line)
                if m and len(m.group(1)) <= heading_level:
                    flush()
            current.append(line)
        flush()

    if title:
        deck_title = title.strip()
    else:
        deck_title = "Slide deck"
        for s in slides:
            h1 = next((ln.strip()[2:].strip() for ln in s.body_lines
                       if re.match(r"^#\s+\S", ln.strip())), None)
            if h1:
                deck_title = h1
                break
    if not slides:
        slides = [Slide(["_(an empty deck)_"], seen)]
    return slides, deck_title


def fence_live(in_fence: bool, marker, line: str) -> bool:
    """True if a line closes the currently open fence (marker is a
    (marker_text, lang) tuple from _fence_marker)."""
    if not in_fence or marker is None:
        return False
    ch = marker[0][0]
    stripped = line.strip()
    return bool(stripped) and set(stripped) <= {ch}


# ---------------------------------------------------------------------------
# Accessibility checks
# ---------------------------------------------------------------------------


def _channel(v: float) -> float:
    v /= 255.0
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def relative_luminance(color: str) -> float:
    """'#rgb', '#rrggbb' or 'rgb(r,g,b)' -> WCAG relative luminance."""
    c = color.strip().lower()
    if c.startswith("#"):
        h = c[1:]
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        if len(h) != 6:
            raise ValueError(f"unsupported color: {color}")
        rgb = [int(h[k:k + 2], 16) for k in (0, 2, 4)]
    elif c.startswith("rgb("):
        rgb = [int(x) for x in re.findall(r"\d+", c)[:3]]
        if len(rgb) != 3:
            raise ValueError(f"unsupported color syntax: {color}")
    else:
        raise ValueError(f"unsupported color syntax: {color}")
    r, g, b = (_channel(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(c1: str, c2: str) -> float:
    l1, l2 = relative_luminance(c1), relative_luminance(c2)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def extract_css_colors(css_text: str) -> dict:
    colors = {}
    for m in re.finditer(r"--([a-z\-0-9]+)\s*:\s*"
                         r"(#[0-9a-fA-F]{3,8}|rgb\([^)]*\))", css_text):
        name = m.group(1)
        val = m.group(2)
        if len(val) == 9 and not val.startswith("rgb") and val.endswith("ff"):
            val = val[:7]  # 8-digit hex: drop alpha channel for the check
        if name in TEXT_KEYS:
            colors[name] = val
    return colors


# palette keys (with underscores, as stored in THEMES)
TEXT_KEYS = ["bg", "fg", "muted", "link", "accent", "head", "code_bg",
             "border", "mark"]


def check_contrast(theme_key: str, extra_css: str = "") -> list:
    """Check WCAG contrast for text-on-background pairs in light + dark."""
    theme = THEMES[theme_key]
    custom = extract_css_colors(extra_css)
    report = []
    for mode in ("light", "dark"):
        palette = dict(theme[mode])
        palette.update({k: v for k, v in custom.items() if k in palette})
        for fg_key, label in TEXT_PAIRS:
            intermediate = ({("muted" if fg_key == "muted"
                              else fg_key): palette["muted"]} if False else None)
            if fg_key == "muted":
                fg_hex = palette["muted"]
            else:
                fg_hex = palette[fg_key]
            try:
                ratio = contrast_ratio(fg_hex, palette["bg"])
            except ValueError as exc:
                report.append({"scope": "contrast", "level": "warn",
                               "text": f"theme '{theme_key}' ({mode}): could "
                                       f"not check {label}: {exc}"})
                continue
            status = "fail" if ratio < 3.0 else ("warn" if ratio < 4.5
                                                 else "ok")
            verdict = {"ok": "OK", "warn": "low", "fail": "FAIL"}[status]
            note = ""
            if status == "warn":
                note = (" - below 4.5:1; acceptable only for very large "
                        "text (3:1 minimum, >=24px/18.66px bold)")
            elif status == "fail":
                note = " - below 3:1, not readable for any text"
            report.append({
                "scope": "contrast", "level": status,
                "text": (f"theme '{theme_key}' ({mode}): {label} contrast "
                         f"{ratio:.2f}:1 {verdict}{note}"),
                "ratio": ratio})
    return report


def check_images(slides) -> list:
    """Flag markdown images that are missing alt text (empty alt)."""
    report = []
    seen: set = set()
    for idx, slide in enumerate(slides, start=1):
        text = "\n".join(slide.lines)
        text = re.sub(r"(`+)([^`]+)\1", "", text)  # ignore code spans
        for m in re.finditer(r"!\[([^\]]*)\]\(([^)\s]+)[^)]*\)", text):
            alt, src = m.group(1).strip(), m.group(2)
            key = (src, bool(alt))
            if key in seen:
                continue
            seen.add(key)
            if not alt:
                report.append({
                    "scope": "images", "level": "warn",
                    "text": (f"slide {idx} ('{slide.title}'): image '{src}' "
                             "has no alt text (![]()). Add a short "
                             "description; plain ![]() is only OK for "
                             "decorative images.")})
            else:
                report.append({
                    "scope": "images", "level": "ok",
                    "text": (f"slide {idx} ('{slide.title}'): image '{src}' "
                             f'alt text: "{alt[:60]}"')})
    return report


def check_headings(slides) -> list:
    report = []
    for idx, slide in enumerate(slides, start=1):
        levels = [len(m.group(1)) for ln in slide.body_lines
                  if (m := re.match(r"^(#{1,6})\s+", ln.strip()))]
        for prev, cur in zip(levels, levels[1:]):
            if cur > prev + 1:
                report.append({
                    "scope": "headings", "level": "warn",
                    "text": (f"slide {idx} ('{slide.title}'): heading level "
                             f"skips from h{prev} to h{cur}; screen readers "
                             "may lose context.")})
    return report


def run_checks(theme_key: str, slides, extra_css: str = "") -> list:
    """Order: contrast, images, headings."""
    report = []
    report += check_contrast(theme_key, extra_css)
    report += check_images(slides)
    report += check_headings(slides)
    return report


def render_report(report) -> str:
    lines = ["ACCESSIBILITY REPORT", "-" * 62]
    counts = {"ok": 0, "warn": 0, "fail": 0}
    for item in report:
        level = item["level"]
        mark = {"ok": "  ok ", "warn": " WARN", "fail": " FAIL"}.get(
            level, " ?? ")
        lines.append(f"{mark} | " + item["text"])
        if level in counts:
            counts[level] += 1
    lines.append("-" * 62)
    total = len(report)
    lines.append(f"{total} checks: {counts['ok']} ok, {counts['warn']} "
                 f"warnings, {counts['fail']} failures")
    if not any(i["scope"] == "images" for i in report):
        lines.append("note: no images found - nothing to check for alt text")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

BASE_CSS = """\
:root {
  --bg: ${bg}; --fg: ${fg}; --muted: ${muted}; --accent: ${accent};
  --link: ${link}; --head: ${head}; --code-bg: ${code_bg};
  --border: ${border}; --mark: ${mark};
  --base-size: ${base_size};
}
html.dark {
  --bg: ${bg_dark}; --fg: ${fg_dark}; --muted: ${muted_dark};
  --accent: ${accent_dark}; --link: ${link_dark}; --head: ${head_dark};
  --code-bg: ${code_bg_dark}; --border: ${border_dark}; --mark: ${mark_dark};
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; height: 100%; }
body {
  background: var(--bg); color: var(--fg);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
  font-size: var(--base-size);
  line-height: 1.55;
}
#deck { height: 100%; }
.slide {
  display: none;
  position: fixed; inset: 0;
  padding: clamp(1.2rem, 5vw, 4rem) clamp(1.4rem, 7vw, 6rem);
  overflow: auto;
}
.slide.active { display: flex; flex-direction: column; justify-content: center; }
.speaker-notes { display: none; }
h1, h2, h3, h4 { color: var(--head); line-height: 1.15; margin: 0 0 0.5em; }
h1 { font-size: clamp(1.9rem, 4.5vw, 3.2rem); }
h2 { font-size: clamp(1.5rem, 3.4vw, 2.4rem); }
h3 { font-size: clamp(1.25rem, 2.6vw, 1.8rem); }
p, li { max-width: 68ch; }
a { color: var(--link); }
strong { color: var(--head); }
code, pre {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.95em;
}
code { background: var(--code-bg); padding: 0.08em 0.35em; border-radius: 4px; }
pre {
  background: var(--code-bg); padding: 0.9em 1.1em; border-radius: 8px;
  overflow: auto; border: 1px solid var(--border); line-height: 1.45;
}
pre code { background: none; padding: 0; font-size: inherit; }
mark { background: var(--mark); color: inherit; padding: 0 0.2em; }
blockquote {
  margin: 1em 0; padding: 0.5em 1.1em; border-left: 4px solid var(--accent);
  background: var(--code-bg); border-radius: 0 8px 8px 0; max-width: 68ch;
}
blockquote p { margin: 0.35em 0; }
table { border-collapse: collapse; margin: 1em 0; font-size: 0.97em; }
th, td { border: 1px solid var(--border); padding: 0.45em 0.8em; }
th { background: var(--code-bg); color: var(--head); }
img { max-width: min(90vw, 780px); max-height: 55vh; border-radius: 8px; }
hr { border: 0; border-top: 2px solid var(--border); margin: 1.2em 0; }
ul, ol { padding-left: 1.4em; }
li { margin: 0.35em 0; }
li > ul, li > ol { margin: 0.3em 0; }
.slide.title-slide h1 { color: var(--accent); }

/* HUD (built-in controls) */
#progress {
  position: fixed; top: 0; left: 0; right: 0; height: 4px;
  background: var(--border); z-index: 30;
}
#progress-bar {
  height: 100%; width: 0; background: var(--accent);
  transition: width 0.18s ease-out;
}
.hud {
  position: fixed; bottom: 0.7rem; right: 0.9rem; z-index: 40;
  display: flex; gap: 0.45rem; align-items: center;
}
.hud button {
  background: var(--code-bg); color: var(--fg);
  border: 1px solid var(--border); border-radius: 8px;
  font: inherit; font-size: 0.92em; padding: 0.32em 0.62em;
  cursor: pointer; min-width: 2.2em;
}
.hud button:hover { border-color: var(--accent); }
#counter {
  background: var(--code-bg); border: 1px solid var(--border);
  border-radius: 8px; padding: 0.32em 0.62em; font-size: 0.92em;
  color: var(--muted); font-variant-numeric: tabular-nums;
}

/* Presenter drawer: notes and timer */
#presenter {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 50;
  background: var(--code-bg); border-top: 2px solid var(--accent);
  color: var(--fg);
  display: none; grid-template-columns: 1fr auto; gap: 1rem;
  padding: 0.8rem 1.2rem 1rem; max-height: 42vh; overflow: auto;
  box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.18);
}
body.presenter #presenter { display: grid; }
#presenter .notes-title {
  font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--muted); margin: 0 0 0.4em;
}
#presenter-notes { font-size: 1.02em; max-width: 70ch; overflow: auto; }
.timer {
  align-self: start; text-align: right; font-variant-numeric: tabular-nums;
}
.timer .clock {
  font-size: 2rem; font-weight: 700; color: var(--head); display: block;
}
.timer .clock.paused { color: var(--muted); }
.timer button {
  background: var(--bg); color: var(--fg);
  border: 1px solid var(--border); border-radius: 8px;
  font: inherit; font-size: 0.85em; padding: 0.3em 0.7em; cursor: pointer;
}
@media (max-width: 640px) {
  .hud { gap: 0.3rem; }
}
:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.slide:focus-visible { outline: none; }
"""

PRINT_CSS = """\
@page { size: landscape; margin: 0.45in; }
@media print {
  html, body { height: auto; background: #fff; color: #111; }
  #progress, .hud, #presenter, .speaker-notes { display: none !important; }
  body { font-size: 17px; }
  #deck { display: block; height: auto; }
  .slide {
    display: block !important; position: static;
    page-break-after: always; break-after: page;
    height: 6.9in; padding: 0.2in 0; overflow: visible;
  }
  .slide.active { display: block !important; }
  .slide h1 { font-size: 30px; }
  .slide h2 { font-size: 24px; }
  .slide h3 { font-size: 20px; }
  .slide p, .slide li, .slide td, .slide th { font-size: 18px; }
  .slide pre, .slide code { font-size: 15px; }
  img { max-height: 4.6in; max-width: 9in; }
  blockquote, table, pre { break-inside: avoid; }
}
"""

DECK_TEMPLATE = string.Template("""\
<!doctype html>
<html lang="$lang">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<meta name="generator" content="mdslide $version by Asdale Dynamics, LLC">
<meta name="color-scheme" content="light dark">
<style>
$base_css
$print_css
$extra_css
</style>
</head>
<body>
<div id="progress" aria-hidden="true"><div id="progress-bar"></div></div>
<main id="deck">
$slides
</main>
<div class="hud">
  <span id="counter">1 / $n</span>
  <button id="prev" title="Previous slide (Left arrow)" aria-label="Previous slide">&#8592;</button>
  <button id="next" title="Next slide (Right arrow)" aria-label="Next slide">&#8594;</button>
  <button id="mode" title="Toggle dark mode (D)" aria-label="Toggle dark mode">&#9680;</button>
  <button id="pres" title="Presenter view: notes and timer (P)" aria-label="Toggle presenter view">P</button>
  <button id="fs" title="Fullscreen (F)" aria-label="Toggle fullscreen">&#9974;</button>
  <button id="pdf" title="Print / save as PDF (Ctrl+P)" aria-label="Print or save as PDF">&#10697;</button>
</div>
<aside id="presenter" aria-label="Presenter view">
  <div>
    <p class="notes-title">Speaker notes &mdash; <span id="pres-slide"></span></p>
    <div id="presenter-notes"></div>
  </div>
  <div class="timer">
    <span class="clock" id="clock">00:00</span>
    <div>
      <button id="tstart" title="Start / pause timer (T)">Start</button>
      <button id="treset" title="Reset timer (R)">Reset</button>
    </div>
  </div>
</aside>
<script>
$script
</script>
</body>
</html>
""")

SLIDE_TEMPLATE = string.Template("""\
  <section class="slide$_title_class" id="$slug" aria-label="Slide $num of $total">
    <div class="slide-body">
$content
    </div>
    <div class="speaker-notes">$notes</div>
  </section>
""")

SCRIPT = """\
(function () {
  "use strict";
  var deck = document.getElementById("deck");
  var slides = [].slice.call(deck.querySelectorAll(".slide"));
  var i = 0;
  var counter = document.getElementById("counter");
  var bar = document.getElementById("progress-bar");
  var notesBox = document.getElementById("presenter-notes");
  var slideTag = document.getElementById("pres-slide");
  var NO_NOTES = "(no notes for this slide \\u2014 add a <!-- note: ... --> comment in the markdown)";

  function show(n) {
    if (n < 0) { n = 0; }
    if (n > slides.length - 1) { n = slides.length - 1; }
    i = n;
    slides.forEach(function (s, k) {
      var active = k === i;
      s.classList.toggle("active", active);
      s.setAttribute("aria-hidden", active ? "false" : "true");
    });
    counter.textContent = (i + 1) + " / " + slides.length;
    bar.style.width = (((i + 1) * 100) / slides.length) + "%";
    renderNotes();
  }
  function renderNotes() {
    var notes = slides[i].querySelector(".speaker-notes");
    var text = notes ? notes.innerHTML.trim() : "";
    notesBox.innerHTML = text ? text : NO_NOTES;
    slideTag.textContent = (i + 1) + ": " + slides[i].id;
  }

  document.getElementById("next").addEventListener("click", function () { show(i + 1); });
  document.getElementById("prev").addEventListener("click", function () { show(i - 1); });
  deck.addEventListener("click", function (e) {
    if (e.target.closest("a, button, img")) { return; }
    var x = e.clientX / window.innerWidth;
    if (x > 0.66) { show(i + 1); }
    else if (x < 0.33) { show(i - 1); }
  });

  var root = document.documentElement;
  var stored = null;
  try { stored = localStorage.getItem("mdslide-mode"); } catch (e) {}
  if (stored === "dark" || (stored === null &&
      window.matchMedia("(prefers-color-scheme: dark)").matches)) {
    root.classList.add("dark");
  }
  function toggleDark() {
    root.classList.toggle("dark");
    try {
      localStorage.setItem("mdslide-mode",
        root.classList.contains("dark") ? "dark" : "light");
    } catch (e) {}
  }

  var clock = document.getElementById("clock");
  var startBtn = document.getElementById("tstart");
  var resetBtn = document.getElementById("treset");
  var running = false, elapsed = 0, tick = null;
  function fmt(s) {
    var m = Math.floor(s / 60), r = s % 60;
    return String(m).padStart(2, "0") + ":" + String(r).padStart(2, "0");
  }
  function draw() { clock.textContent = fmt(elapsed); }
  function setBtn() {
    startBtn.textContent = running ? "Pause" : "Start";
    clock.classList.toggle("paused", !running);
  }
  startBtn.addEventListener("click", function () {
    running = !running;
    if (running) {
      tick = setInterval(function () { elapsed += 1; draw(); }, 1000);
    } else if (tick) { clearInterval(tick); tick = null; }
    setBtn();
  });
  resetBtn.addEventListener("click", function () {
    elapsed = 0; draw();
    if (running && tick) { clearInterval(tick); tick = null; }
    running = false;
    setBtn();
  });

  function togglePresenter() {
    document.body.classList.toggle("presenter");
    if (document.body.classList.contains("presenter")) { renderNotes(); }
  }
  document.getElementById("pres").addEventListener("click", togglePresenter);
  document.getElementById("mode").addEventListener("click", toggleDark);
  document.getElementById("fs").addEventListener("click", function () {
    if (document.fullscreenElement) {
      if (document.exitFullscreen) { document.exitFullscreen(); }
    } else if (document.documentElement.requestFullscreen) {
      document.documentElement.requestFullscreen();
    }
  });
  document.getElementById("pdf").addEventListener("click", function () {
    window.print();
  });

  document.addEventListener("keydown", function (e) {
    if (e.target && /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) { return; }
    switch (e.key) {
      case "ArrowRight": case "PageDown": case " ": case "Enter":
        e.preventDefault(); show(i + 1); break;
      case "ArrowLeft": case "PageUp":
        e.preventDefault(); show(i - 1); break;
      case "Home": e.preventDefault(); show(0); break;
      case "End": e.preventDefault(); show(slides.length - 1); break;
      case "d": case "D": toggleDark(); break;
      case "p": case "P": togglePresenter(); break;
      case "t": case "T": startBtn.click(); break;
      case "r": case "R": resetBtn.click(); break;
      case "f": case "F": document.getElementById("fs").click(); break;
    }
  });

  show(0);
})();
"""


def theme_css(theme_key: str) -> str:
    """Substitute the theme palette into the base stylesheet."""
    t = THEMES[theme_key]
    light, dark = t["light"], t["dark"]
    mapping = {}
    for key in TEXT_KEYS:
        mapping[key] = light[key]
        mapping[key + "_dark"] = dark[key]
    mapping["base_size"] = "1.45rem" if theme_key == "large-print" else "1.05rem"
    return string.Template(BASE_CSS).substitute(mapping)


def build_deck(slides, deck_title: str, theme_key: str, lang: str = "en",
               extra_css: str = "") -> str:
    fragments = []
    total = len(slides)
    for num, slide in enumerate(slides, start=1):
        title_class = " title-slide" if (num == 1
                                          and slide.is_title_slide) else ""
        notes = esc(slide.notes_markdown)
        while "\n\n" in notes:
            notes = notes.replace("\n\n", "<br><br>")
        remaining = notes.replace("\n", "<br>")
        fragments.append(SLIDE_TEMPLATE.substitute(
            _title_class=title_class, slug=slide.slug, num=num, total=total,
            content=slide.content_html(), notes=remaining))
    return DECK_TEMPLATE.substitute(
        lang=esc(lang), title=esc(deck_title), version=__version__,
        base_css=theme_css(theme_key), print_css=PRINT_CSS,
        extra_css=extra_css or "", slides="\n".join(fragments), n=total,
        script=SCRIPT)


def export_notes(slides, deck_title: str) -> str:
    out = [f"# Speaker notes — {deck_title}", "",
           f"_{len(slides)} slides. Generated by mdslide "
           f"{__version__} (Asdale Dynamics, LLC)._", ""]
    for num, slide in enumerate(slides, start=1):
        out.append(f"## Slide {num} — {slide.title}")
        out.append("")
        if slide.notes_markdown:
            out.append(slide.notes_markdown)
        else:
            out.append("_(no notes)_")
        out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="mdslide",
        description="Convert a Markdown outline into a self-contained HTML "
                    "slide deck (offline, pure Python, no build step). "
                    "Part of Asdale Dynamics, LLC's beginner-friendly "
                    "toolkit.")
    parser.add_argument("input", help="Markdown file to convert")
    parser.add_argument("-o", "--output", default=None,
                        help="output .html file (default: input with .html)")
    parser.add_argument("--title", default=None,
                        help="deck title (default: first '#' heading)")
    parser.add_argument("--theme", default="default", choices=sorted(THEMES),
                        help="built-in theme (default: 'default')")
    parser.add_argument("--css", default=None, metavar="FILE",
                        help="extra CSS file, inlined after the theme "
                             "(colors via --bg/--fg/--muted/--accent/--link "
                             "variables are accessibility-checked too)")
    parser.add_argument("--split", default="hr", choices=["hr", "headings"],
                        help="slide separator: '---' rules (default) or "
                             "headings up to --heading-level")
    parser.add_argument("--heading-level", type=int, default=2, choices=[1, 2, 3],
                        help="with --split headings: new slide at h1, h2, "
                             "or h3 (default 2)")
    parser.add_argument("--lang", default="en",
                        help="value for the html lang attribute")
    parser.add_argument("--check-only", action="store_true",
                        help="parse the deck, run accessibility checks, "
                             "and exit; exit code 1 on contrast failures")
    parser.add_argument("--export-notes", default=None, metavar="FILE",
                        help="also write speaker notes to a Markdown file")
    parser.add_argument("--report", default=None, metavar="FILE",
                        help="write the accessibility report to a text file")
    parser.add_argument("--version", action="version",
                        version=f"mdslide {__version__}")
    args = parser.parse_args(argv)

    src = Path(args.input)
    if not src.exists():
        print(f"mdslide: input file not found: {src}", file=sys.stderr)
        return 2
    text = src.read_text(encoding="utf-8")

    slides, deck_title = split_slides(
        text, mode=args.split, heading_level=args.heading_level,
        title=args.title)

    extra_css = ""
    if args.css:
        css_path = Path(args.css)
        if not css_path.exists():
            print(f"mdslide: css file not found: {css_path}", file=sys.stderr)
            return 2
        extra_css = css_path.read_text(encoding="utf-8")

    report = run_checks(args.theme, slides, extra_css)
    report_text = render_report(report)

    if args.report:
        Path(args.report).write_text(report_text + "\n", encoding="utf-8")

    if args.check_only:
        print(report_text)
        if any(i["level"] == "fail" for i in report):
            print()
            print("mdslide: accessibility FAILURES found (see above).")
            return 1
        return 0

    output = Path(args.output) if args.output else src.with_suffix(".html")
    deck_html = build_deck(slides, deck_title, args.theme, args.lang,
                           extra_css)
    output.write_text(deck_html, encoding="utf-8")
    print(report_text)
    print()
    print(f'Wrote {output} ({len(slides)} slides, title "{deck_title}")')
    if args.export_notes:
        notes_path = Path(args.export_notes)
        notes_path.write_text(export_notes(slides, deck_title),
                              encoding="utf-8")
        print(f"Wrote {notes_path}")
    if any(i["level"] in ("warn", "fail") for i in report):
        print("note: the accessibility report above has warnings or "
              "failures - the deck still builds, but consider fixing "
              "them for your audience.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
