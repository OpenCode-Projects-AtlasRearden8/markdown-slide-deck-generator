# STATUS.md — mdslide

*Marked complete: 2026-11-03. Built and committed by Asdale Dynamics, LLC.*

## What was built

**mdslide** — a pure-Python, offline, zero-build-step tool that converts a
Markdown outline into a **self-contained HTML slide deck**. One file
(`mdslide.py`, ~1,180 lines, standard library only; needs Python 3.8+).

Delivered features (all working, per verification below):

- **Markdown parsing**: headings, paragraphs, bold/italic/strikethrough,
  code spans, fenced code blocks, bullet/ordered lists with nesting,
  blockquotes, GFM tables, images, links, autolinks, rules. Raw HTML is
  escaped so decks can't inject scripts.
- **Slide splitting**: `---` rules (default) or `--split headings` with
  `--heading-level 1..3`.
- **Presenter notes**: `<!-- note: ... -->` or any HTML comment,
  multi-line supported.
- **Presenter drawer** (key `P`): current slide's notes + a run timer
  with start/pause (`T`) and reset (`R`).
- **Keyboard navigation**: arrows, PageUp/Down, Space/Enter, Home/End;
  on-screen HUD buttons for mouse users; click left/right third of the
  slide to navigate; fullscreen (`F`); progress bar; slide counter.
- **Print-to-PDF**: `@media print` stylesheet — one slide per page, UI
  hidden, large print-friendly type (18px body, 30px h1); printer button.
- **Dark mode**: toggle button / key `D`, respects `prefers-color-scheme`,
  persisted in localStorage.
- **5 built-in themes** (`default`, `forest`, `midnight`,
  `high-contrast`, `large-print`), each light+dark (`midnight` always
  dark), all WCAG-passing for body text.
- **Custom CSS**: `--css file` is inlined (deck stays single-file and
  offline); theme CSS variables are recognized and accessibility-checked.
- **Accessibility checks** (`--check-only`, `--report`): WCAG contrast
  for body/secondary/link/accent colors vs background in light *and*
  dark variants (4.5:1 pass, <3:1 fail), missing image alt text with
  slide numbers, skipped heading levels. Exit code 1 on failures.
- **Speaker-notes export**: `--export-notes notes.md` writes a Markdown
  file listing every slide with its notes.
- **Safety/local-first**: no network calls, no credentials, no
  telemetry; decks are single HTML files.

Also included: `README.md` (friendly plain-English guide), `tests/`
(53 tests), `examples/` (4 decks + 1 deliberately-bad theme CSS),
MIT `LICENSE`, `.gitignore`.

## How to run it

```bash
# convert (writes input-name.html)
python3 mdslide.py examples/ai-basics.md

# pick a look, keep a notes file
python3 mdslide.py my-deck.md --theme forest \
    --export-notes my-notes.md --report a11y.txt

# audit accessibility only (exit 1 on contrast failures)
python3 mdslide.py my-deck.md --check-only

# run the tests (no installs needed)
python3 -m unittest discover -s tests
```

Then open the generated `.html` in any browser: `Right`/`Left` to
navigate, `P` for notes + timer, `D` for dark mode, printer button
(or `Ctrl+P`) to save as PDF.

## Verification results (2026-11-03, Python 3.13.5)

| Check | Result |
|---|---|
| `python3 -m unittest discover -s tests` | **53 tests ran in 0.013s — OK** |
| `python3 -m py_compile mdslide.py` | OK, no warnings |
| Build `examples/ai-basics.md` | rc=0, 7 slides, report: 8 ok / 0 warn / 0 fail |
| Build `examples/features-tour.md` | rc=0, 8 slides, report: 9 ok / 0 warn / 0 fail |
| Build `examples/split-headings.md --split headings` | rc=0, 4 slides |
| `--check-only` on `examples/needs-work.md --css bad-theme.css` | rc=1 with 4 failures (intentional demo) |
| All 5 themes | build rc=0 each; contrast checks pass for all |
| Generated deck JS | syntax-verified with `node --check` for all 5 themes |
| Notes export | verified for all 3 buildable examples |
| No external resources in deck HTML | asserted by test (no http(s), no stylesheet links) |
| `LICENSE` copyright line | exactly `Copyright (c) 2026 Asdale Dynamics, LLC` |

## Known gaps (honest list)

- **Markdown subset is deliberate**: no footnotes, definition lists,
  nested blockquotes, task-list checkboxes, or image *click-to-zoom*.
  Tables need the GFM `|` form with a `---` separator row.
- **Print page size** assumes landscape letter/A4; other page sizes
  may leave a small gap below slides (browser "scale" fixes it).
- **`--check-only` contrast coverage** covers theme palette variables,
  not per-element inline styling beyond the recognized variables.
- **Presenter view** shares the window (fixed drawer), not a second
  window/monitor like PowerPoint's dual-display mode.
- **No syntax highlighting** inside code blocks (plain `<pre>`).
- **Theme toggle button** is a single ◐ glyph; no React-style theming
  UI (by design — zero dependencies).
- **Timer** counts upward only (no countdown mode).
- Decks reference images by relative path; images are **not** embedded
  into the HTML file (keeping output legible). Alt-text checks still
  flag them correctly.
- Windows line endings (`\r\n`) are normalized but mixed encodings
  beyond UTF-8 are not auto-detected.

## Repo state

- Git initialized; single plain commit `a290afb` "mdslide: markdown
  outline to self-contained HTML slide decks" (no co-author trailers).
- Nothing pushed, no remotes, nothing published, no secrets or
  personal data in files beyond the requested LLC credit.
