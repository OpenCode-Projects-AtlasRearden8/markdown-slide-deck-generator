"""Tests for mdslide — plain stdlib unittest, run with:

    python3 -m unittest discover -s tests

Copyright (c) 2026 Asdale Dynamics, LLC
"""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import mdslide  # noqa: E402


class InlineMarkdownTests(unittest.TestCase):
    def test_strong_em_del_code(self):
        self.assertEqual(mdslide.inline("**b** *i* ~~s~~ `c`"),
                         "<strong>b</strong> <em>i</em> "
                         "<del>s</del> <code>c</code>")

    def test_link_and_autolink(self):
        self.assertEqual(mdslide.inline("[x](https://a.b)"),
                         '<a href="https://a.b">x</a>')
        self.assertEqual(mdslide.inline("<https://a.b>"),
                         '<a href="https://a.b">https://a.b</a>')

    def test_image(self):
        got = mdslide.inline("![alt text](img/cat.png)")
        self.assertIn('alt="alt text"', got)
        self.assertIn('src="img/cat.png"', got)

    def test_raw_html_is_escaped(self):
        got = mdslide.inline('<img onerror="evil()">go')
        self.assertNotIn("<img", got)
        self.assertIn("&lt;img", got)

    def test_code_span_protects_markup(self):
        got = mdslide.inline("`<b>&</b>*x*`")
        self.assertIn("<code>&lt;b&gt;&amp;&lt;/b&gt;*x*</code>", got)


class BlockMarkdownTests(unittest.TestCase):
    def blocks(self, md):
        return mdslide.parse_blocks(md.split("\n"))

    def test_heading_levels(self):
        self.assertEqual(
            self.blocks("# h1\n## h2\n### h3"),
            "<h1>h1</h1>\n<h2>h2</h2>\n<h3>h3</h3>")

    def test_paragraph_joins_lines(self):
        html_out = self.blocks("line one\nline two")
        self.assertEqual(html_out, "<p>line one<br>line two</p>")

    def test_lists_mixed(self):
        html_out = self.blocks("- a\n- b\n\n1. x\n2. y")
        self.assertIn("<ul><li>a</li><li>b</li></ul>", html_out)
        self.assertIn("<ol><li>x</li><li>y</li></ol>", html_out)

    def test_nested_list(self):
        html_out = self.blocks("- a\n  - a1")
        self.assertIn("<ul><li>a\n<ul><li>a1</li></ul></li></ul>", html_out)

    def test_blockquote(self):
        html_out = self.blocks("> quote **bold**")
        self.assertIn("<blockquote>", html_out)
        self.assertIn("<strong>bold</strong>", html_out)

    def test_fenced_code_not_parsed(self):
        html_out = self.blocks("```\n# not a heading\n**bold**\n```")
        self.assertIn("<pre><code>", html_out)
        self.assertNotIn("not a heading</h1>", html_out)
        self.assertIn("**bold**", html_out)

    def test_fenced_code_language(self):
        html_out = self.blocks("```python\nx = 1\n```")
        self.assertIn('class="lang-python"', html_out)

    def test_table_with_alignment(self):
        html_out = self.blocks("| A | B |\n|---|:-:|\n| 1 | 2 |")
        self.assertIn('style="text-align:center"', html_out)
        self.assertIn("<thead>", html_out)

    def test_hr(self):
        self.assertIn("<hr>", self.blocks("***"))

    def test_unclosed_fence_keeps_code(self):
        html_out = self.blocks("```text\nstill code")
        self.assertIn("still code", html_out)


class SlideSplittingTests(unittest.TestCase):
    def test_split_on_hr(self):
        slides, title = mdslide.split_slides("# Deck\nA\n\n---\n\nB\n")
        self.assertEqual(len(slides), 2)
        self.assertEqual(title, "Deck")

    def test_split_on_headings(self):
        md = "Intro before first heading\n\n# One\n\n## Sublook\n\nbody\n\n# Two\n"
        slides, _ = mdslide.split_slides(md, mode="headings",
                                         heading_level=1)
        # any preamble before the first heading becomes its own slide
        self.assertEqual([s.title for s in slides],
                         ["(slide)", "One", "Two"])
        self.assertIn("Intro before", slides[0].body_lines[0])

    def test_headings_mode_respects_heading_level(self):
        md = "# One\n\na\n\n## Sub\n\nb\n"
        # level 1: only '#' starts a slide; '## Sub' stays inside
        slides, _ = mdslide.split_slides(md, mode="headings",
                                         heading_level=1)
        self.assertEqual([s.title for s in slides], ["One"])
        self.assertIn("## Sub", slides[0].body_lines)

    def test_hr_inside_code_fence_does_not_split(self):
        md = "# Deck\n```\n---\n```\n"
        slides, _ = mdslide.split_slides(md)
        self.assertEqual(len(slides), 1)
        html_out = slides[0].content_html()
        self.assertIn("<pre><code>", html_out)
        self.assertIn("---", html_out)

    def test_explicit_title_beats_heading(self):
        _, title = mdslide.split_slides("# Heading\n", title="Given")
        self.assertEqual(title, "Given")

    def test_empty_input_makes_one_placeholder_slide(self):
        slides, _ = mdslide.split_slides("")
        self.assertEqual(len(slides), 1)

    def test_unique_slugs(self):
        md = "# Same\n\n---\n\n# Same\n"
        slides, _ = mdslide.split_slides(md)
        slugs = [s.slug for s in slides]
        self.assertEqual(len(set(slugs)), 2)
        self.assertEqual(slugs[1], "same-2")


class NotesTests(unittest.TestCase):
    def test_note_comment_extracted(self):
        md = "## S\nbody\n<!-- note: speak calmly -->\n"
        slides, _ = mdslide.split_slides(md)
        self.assertEqual(slides[0].notes_markdown, "speak calmly")

    def test_notes_alias_and_multiline(self):
        md = "## S\n<!--\nnotes: line one\nline two\n-->\n"
        slides, _ = mdslide.split_slides(md)
        self.assertEqual(slides[0].notes_markdown,
                         "line one\nline two")

    def test_comment_stays_out_of_content(self):
        md = "## S\n<!-- note: whisper -->body\n"
        slides, _ = mdslide.split_slides(md)
        html_out = slides[0].content_html()
        self.assertNotIn("whisper", html_out)

    def test_export_notes(self):
        md = "# Deck\n<!-- note: n1 -->\n\n---\n\n# Second\n<!-- note: n2 -->\n"
        slides, deck_title = mdslide.split_slides(md)
        out = mdslide.export_notes(slides, deck_title)
        self.assertIn("# Speaker notes — Deck", out)
        self.assertIn("## Slide 1 — Deck", out)
        self.assertIn("n2", out)
        self.assertIn("Asdale Dynamics, LLC", out)


class ContrastTests(unittest.TestCase):
    def test_black_white_is_21(self):
        self.assertAlmostEqual(mdslide.contrast_ratio("#000", "#fff"), 21.0,
                               places=2)

    def test_same_color_is_one(self):
        self.assertAlmostEqual(mdslide.contrast_ratio("#333333", "#333333"),
                               1.0)

    def test_rgb_function_supported(self):
        self.assertAlmostEqual(mdslide.contrast_ratio(
            "rgb(0,0,0)", "rgb(255,255,255)"), 21.0, places=2)

    def test_bad_color_raises_valueerror(self):
        with self.assertRaises(ValueError):
            mdslide.contrast_ratio("#12345", "#fff")

    def test_all_builtin_themes_pass(self):
        for key in mdslide.THEMES:
            for r in mdslide.check_contrast(key):
                if r["scope"] == "contrast":
                    self.assertNotEqual(r["level"], "fail", r["text"])

    def test_low_contrast_custom_css_fails(self):
        css = ":root{ --fg: #888888; --bg: #dddddd; }"
        report = mdslide.check_contrast("default", extra_css=css)
        fails = [r for r in report if r["level"] == "fail"]
        self.assertTrue(fails)
        self.assertIn("Body text", fails[0]["text"])

    def test_extract_css_colors(self):
        colors = mdslide.extract_css_colors(
            ".x { --fg: #abc; --bg: rgb(1, 2, 3); --skip: red; }")
        self.assertEqual(colors["fg"], "#abc")
        self.assertEqual(colors["bg"], "rgb(1, 2, 3)")
        self.assertNotIn("skip", colors)


class CheckTests(unittest.TestCase):
    def test_missing_alt_warns_with_slide_number(self):
        md = "# Deck\n![alt good](a.png)\n\n---\n\n# More\n![](b.png)\n"
        slides, _ = mdslide.split_slides(md)
        report = mdslide.check_images(slides)
        warns = [r for r in report if r["level"] == "warn"]
        oks = [r for r in report if r["level"] == "ok"]
        self.assertEqual(len(warns), 1)
        self.assertIn("slide 2", warns[0]["text"])
        self.assertEqual(len(oks), 1)

    def test_duplicate_image_without_alt_warns_once(self):
        md = "# Deck\n![](a.png)\n\n---\n\n# More\n![](a.png)\n"
        slides, _ = mdslide.split_slides(md)
        warns = [r for r in mdslide.check_images(slides) if r["level"] == "warn"]
        self.assertEqual(len(warns), 1)

    def test_heading_skip_warns(self):
        md = "# Deck\n## h2\n#### h4\n"
        slides, _ = mdslide.split_slides(md)
        warns = [r for r in mdslide.check_headings(slides)
                 if r["level"] == "warn"]
        self.assertTrue(warns)

    def test_check_only_fails_on_bad_contrast(self):
        md_path = Path(tempfile.mkstemp(suffix=".md")[1])
        css_path = Path(tempfile.mkstemp(suffix=".css")[1])
        css_path.write_text(":root{ --fg: #999999; --bg: #eeeeee; }")
        md_path.write_text("# Deck\n")
        rc = mdslide.main([str(md_path), "--check-only",
                           "--css", str(css_path)])
        self.assertEqual(rc, 1)
        md_path.unlink()
        css_path.unlink()

    def test_check_only_ok_returns_zero(self):
        md_path = Path(tempfile.mkstemp(suffix=".md")[1])
        md_path.write_text("# Clean deck\n\nNo issues here.\n")
        rc = mdslide.main([str(md_path), "--check-only"])
        self.assertEqual(rc, 0)
        md_path.unlink()


class RenderTests(unittest.TestCase):
    MD = ("# Deck\nintro\n<!-- note: speak up -->\n\n---\n\n"
          "## Second\n- item\n\n```\ncode here\n```\n")

    def setUp(self):
        self.slides, self.deck_title = mdslide.split_slides(self.MD)
        self.out = mdslide.build_deck(self.slides, self.deck_title,
                                      "forest")

    def test_contains_core_ui(self):
        for needle in ("id=\"progress-bar\"", "id=\"counter\"", "id=\"pres\"",
                       "id=\"pdf\"", "id=\"presenter\"",
                       "id=\"tstart\"", "id=\"treset\"", "aria-label",
                       "color-scheme", "prefers-color-scheme",
                       "mdslide-mode"):
            self.assertIn(needle, self.out, needle)

    def test_notes_embedded_and_hidden(self):
        self.assertIn("speak up", self.out)
        self.assertIn(".speaker-notes { display: none; }", self.out)

    def test_no_external_resources(self):
        self.assertNotIn("http://", self.out)
        self.assertNotIn("https://", self.out)
        self.assertNotIn("srcset=", self.out)
        self.assertNotIn("link rel=\"stylesheet\"", self.out)

    def test_theme_and_print_css_present(self):
        self.assertIn("@media print", self.out)
        self.assertIn("@page", self.out)
        self.assertIn("page-break-after: always", self.out)

    def test_large_print_theme_bigger_base(self):
        out = mdslide.build_deck(self.slides, self.deck_title,
                                 "large-print")
        self.assertIn("--base-size: 1.45rem", out)

    def test_slide_aria_labels(self):
        self.assertIn('aria-label="Slide 1 of 2"', self.out)

    def test_keys_documented_in_titles(self):
        for needle in ("Toggle dark mode (D)", "Presenter view: notes and "
                       "timer (P)"):
            self.assertIn(needle, self.out)


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mdslide-test-"))
        self.deck = self.tmp / "deck.md"
        self.deck.write_text("# K\nintro\n\n---\n\n# Two\nbody\n")

    def wc(self, sub, extra=()):
        return mdslide.main([str(self.deck), *sub, *extra])

    def test_build_writes_html(self):
        out = self.tmp / "d.html"
        self.assertEqual(self.wc(["-o", str(out)]), 0)
        text = out.read_text()
        self.assertIn("<!doctype html>", text)
        self.assertIn("K</h1>", text)

    def test_export_notes(self):
        notes = self.tmp / "notes.md"
        self.wc(["-o", str(self.tmp / "d.html")],
                ("--export-notes", str(notes)))
        self.assertIn("# Speaker notes", notes.read_text())

    def test_report_file(self):
        rep = self.tmp / "r.txt"
        self.wc(["-o", str(self.tmp / "d.html")], ("--report", str(rep)))
        self.assertIn("ACCESSIBILITY REPORT", rep.read_text())

    def test_missing_input_returns_2(self):
        self.assertEqual(mdslide.main([str(self.tmp / "nope.md")]), 2)

    def test_missing_css_returns_2(self):
        self.assertEqual(self.wc(["-o", str(self.tmp / "d.html")],
                                 ("--css", str(self.tmp / "no.css"))), 2)

    def test_check_only_writes_no_html(self):
        out = self.tmp / "d.html"
        rc = self.wc(["--check-only"])
        self.assertEqual(rc, 0)
        self.assertFalse(out.exists())

    def test_examples_build_cleanly(self):
        examples = sorted((ROOT / "examples").glob("*.md"))
        self.assertTrue(examples, "example decks must ship")
        for ex in examples:
            out = self.tmp / (ex.stem + ".html")
            rc = mdslide.main([str(ex), "-o", str(out), "--export-notes",
                               str(self.tmp / (ex.stem + "-notes.md"))])
            self.assertEqual(rc, 0, ex.name)
            self.assertTrue(out.exists())
            self.assertIn("<!doctype html>", out.read_text())

    def test_needs_work_example_fails_checks(self):
        bad = ROOT / "examples" / "needs-work.md"
        css = ROOT / "examples" / "bad-theme.css"
        self.assertTrue(bad.exists() and css.exists(),
                        "a11y example deck + bad theme must ship")
        rc = mdslide.main([str(bad), "--check-only", "--css", str(css)])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
