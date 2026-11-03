# mdslide

Turn a Markdown outline into **self-contained HTML slides** — one Python
file, zero dependencies, zero build step, works fully offline.

Explain things like a friend would: plain English, step by step, never
condescending. mdslide is built in that spirit by
**Asdale Dynamics, LLC** (Dylan Asdale) for beginner-friendly AI
education — but it's handy for *any* deck outline.

```text
your-outline.md  --(pure Python)-->  your-outline.html  --(browser)-->  talk
                                                          \-->  print to PDF
```

## Quick start

```bash
# needs only Python 3.8+ (stdlib only). No install, no npm, no internet.
python3 mdslide.py my-deck.md

# pick a look
python3 mdslide.py my-deck.md --theme forest -o talk.html

# audit before you present
python3 mdslide.py my-deck.md --check-only
```

A tiny example without install: try the included decks:

```bash
python3 mdslide.py examples/ai-basics.md
python3 mdslide.py examples/features-tour.md
python3 mdslide.py examples/split-headings.md --split headings
python3 mdslide.py examples/needs-work.md --check-only --css examples/bad-theme.css
```

## Writing a deck

A plain Markdown file is a deck. Start a new slide with a `---` rule,
or split on headings with `--split headings`:

```markdown
# My Talk

Opening line.

---

## The point

- plain English
- short slides
- notes in comments

<!-- note: this HTML comment is a presenter note -->
```

### Markdown support (deliberately small)

Headings, paragraphs, bold/italic, `code spans`, fenced code blocks,
bullet and numbered lists (with nesting), blockquotes, simple GFM
tables, images, links, autolinks, strikethrough, and horizontal rules.
Raw HTML is **escaped on purpose** — decks stay safe.

### Presenter notes

Write `<!-- note: your note -->` (or `<!-- notes: ... -->`, or any HTML
comment) anywhere in a slide. They appear in the presenter drawer and
export to a separate Markdown file when you run with
`--export-notes notes.md`.

## Presenting

Open the built `.html` in any browser. Keyboard:

| Action                | Keys                          |
|-----------------------|-------------------------------|
| next / previous slide | `Right` / `Left`, `PageUp`/`Down` |
| next slide            | `Space`, `Enter`              |
| first / last slide    | `Home` / `End`                |
| presenter view (notes + timer) | `P`                  |
| timer start-pause / reset | `T` / `R`                 |
| dark mode             | `D`                           |
| fullscreen            | `F`                           |
| print / save as PDF   | printer button or `Ctrl+P`    |

You can also click the right or left side of a slide to move forward
or back. The HUD (bottom-right) has buttons for all the same things,
so a mouse-only friend is covered too.

### Presenter view

Press `P` to open a drawer with the current slide's speaker notes and
a running timer (start/pause/reset). It stays fixed at the bottom so
you can glance without leaving the slide.

### Dark mode

`D` toggles it; mdslide respects your OS `prefers-color-scheme`
setting until you toggle, then remembers your choice locally. No
accounts, no analytics, no network requests — ever.

## Print to PDF

Click the printer button (or `Ctrl+P`) and choose *Save as PDF*.
The print stylesheet puts one slide per page, hides UI chrome, and
bumps type sizes for readable handouts. Slide type is large-print
friendly by default in print.

## Themes

Built-in themes: `default` (warm paper), `forest`, `midnight` (always
dark), `high-contrast`, `large-print` (big type, roomy spacing).
Every theme has a light *and* dark variant (except `midnight`).

Bring your own polish with a CSS file — it's inlined so the deck
stays a single file and fully offline:

```bash
python3 mdslide.py my-deck.md --css my-tweaks.css
```

Recolor through CSS variables: `--bg`, `--fg`, `--muted`, `--accent`,
`--link`, `--head`, `--code-bg`, `--border`, `--mark`. mdslide knows
these names and runs contrast checks on your values too.

## Accessibility checks

```bash
python3 mdslide.py my-deck.md --check-only
```

- **Contrast** (WCAG): body, secondary, link, and accent colors
  against the background, for light *and* dark variants of your
  theme's palette.
- **Alt text**: images written as `![](pic.png)` are flagged with the
  slide number; purely decorative images are the reader's call, so
  these are warnings, not failures.
- **Heading order**: jumps like h2 → h4 earn a warning.

Every built-in theme passes WCAG contrast for body text. The check
reports `ok` / `warn` / `fail` lines, honors `4.5:1` for normal body
text (3:1 soft-floor for very large type with a warning), and
`--check-only` exits `1` when there are genuine failures — useful in
CI for your docs.

## Speaker notes export

```bash
python3 mdslide.py my-deck.md --export-notes notes.md
```

`notes.md` lists every slide title with its notes — handy to rehearse
from paper or keep in your author workflows.

## CLI reference

| Option | Meaning |
|---|---|
| `-o, --output FILE` | output path (default: `.md` → `.html`) |
| `--title TEXT` | deck title (default: first `#` heading) |
| `--theme NAME` | built-in theme |
| `--css FILE` | extra CSS, inlined |
| `--split {hr,headings}` | slide separator method |
| `--heading-level 1-3` | with `--split headings` |
| `--lang LL` | `html lang` (default `en`) |
| `--check-only` | accessibility audit, no HTML written |
| `--export-notes FILE` | speaker notes as Markdown |
| `--report FILE` | accessibility report as text |

```bash
python3 mdslide.py --help
python3 mdslide.py --version     # mdslide 1.0.0
```

## Tests

Plain `unittest`, still zero-install:

```bash
python3 -m unittest discover -s tests
```

## Layout of this folder

```text
mdslide.py                 the whole tool (one file)
tests/test_mdslide.py      53 unit/CLI tests
examples/                  ready-to-run example decks
  ai-basics.md             friendly AI intro (companion to The Massive AI Manual)
  features-tour.md         everything mdslide does, demonstrated
  split-headings.md        --split headings demo
  needs-work.md + bad-theme.css   deliberate accessibility failures
```

## Design notes

- **Local-first**: no accounts, no telemetry, no network calls, no
  secrets. Decks are single HTML files you can email, archive, or put
  on a USB stick.
- **Safe by default**: raw HTML in markdown is escaped; only
  mdslide-generated markup is emitted.
- **Friendly for beginners**: the tool explains itself via `--help`
  and the reports use plain sentences, not codes.

## Why an LLC made this

Dylan Asdale is a registered nurse turned AI author and founder of
**Asdale Dynamics, LLC** — the LLC behind
[dylanasdale.github.io](https://dylanasdale.github.io) and the book
*The Massive AI Manual*. The mission: beginner-friendly AI education
that explains things the way a friend would. mdslide fits the "open
tools the LLC can publish or sell" box: small, tested, accessible.

If an orphaned sentence in the docs made you smile, that's the brand.

## License

MIT — see [LICENSE](LICENSE).
Copyright (c) 2026 Asdale Dynamics, LLC.
