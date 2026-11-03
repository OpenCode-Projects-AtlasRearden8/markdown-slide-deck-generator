# mdslide Feature Tour

A deck showing everything mdslide does. Read the source of this file
side by side with the built deck!

---

## Use `---` to break slides

Every `---` rule in your markdown starts a new slide (that's the
default `--split hr` mode).

Prefer splitting **on headings** instead? Run with
`--split headings` and slides start at every `#`/`##`.

---

## Markdown you can use

- **bold**, *italic*, ~~strike~~, `inline code`
- lists, [links](https://dylanasdale.github.io), and blockquotes:

> mdslide turns an outline into a deck.
> No build step. Pure Python. Fully offline.

| Feature | Key |
|---|---|
| Next / previous slide | `Right` / `Left` |
| Advance (next slide) | `Space` or `Enter` |
| Home / End | first / last slide |
| Presenter view | `P` |
| Timer start-pause / reset | `T` / `R` |
| Dark mode | `D` |
| Fullscreen | `F` |
| Print to PDF | button or `Ctrl+P` |

<!-- note: Demo each keyboard shortcut one by one. Pause on the presenter view so people see the timer running. -->

---

## Code blocks render safely

```python
def greet(who: str) -> str:
    return f"Hello, {who}!"
```

Raw HTML in your markdown is **escaped** on purpose, so a deck
written by a friend can't inject scripts.

---

## Presenter notes travel with you

Write `<!-- note: ... -->` comments anywhere in a slide and they
become speaker notes in the presenter drawer - then export them:

    python3 mdslide.py deck.md --export-notes notes.md

<!-- note: Show the drawer with P, start the timer with T, then export notes live. Mention the notes file keeps the slide titles. -->

---

## Dark mode, themes, and large print

Press `D` for dark mode (mdslide remembers your choice).

Text decks are for reading: run with `--theme large-print` for a
big, roomy type size, or `--theme high-contrast` for maximum
readability. Add your own polish with `--css my-tweaks.css`.

---

## Printing to PDF

Click the printer button (or press `Ctrl+P`) and choose
**Save as PDF**. Slide type prints large, one slide per page.

![A friendly line drawing of a printer, decorative placeholder](images/placeholder-printer.png)

<!-- note: Users without that image file will see a broken image icon - replace images/placeholder-printer.png with a real picture, or delete the line. -->

---

## Accessibility checks, built in

Run with `--check-only` to audit your deck before presenting:

- **Contrast** - every theme's text colors against its background,
  in WCAG ratios, light *and* dark variants
- **Alt text** - images like `![](pic.png)` with no alt text get
  flagged with the slide number
- **Heading order** - skipped heading levels get a warn

mdslide walks through AI like a friend - and thanks you for keeping
the deck friendly for everybody reading it.
