# Deck That Needs Work

This example deliberately fails mdslide's accessibility checks so
you can see what the warnings look like:

    python3 mdslide.py examples/needs-work.md --check-only --css examples/bad-theme.css

Exit code 1, failures listed.

---

## Low-contrast text

The custom css file in this repo sets body text to a light gray on a
barely-lighter background. mdslide checks custom css colors too:
`--fg`, `--bg`, `--muted`, `--accent`, `--link`.

<!-- note: Explain that 3:1 is the absolute floor and 4.5:1 is the real goal for body text. -->

---

## Images without alt text

Below, the first image has no alt text and the second is missing any
description for screen readers:

![](ipsum-1.png)
![](ipsum-2.png)

> Fix: swap `![](ipsum-1.png)` for `![Two friends sharing notes](ipsum-1.png)`.

---

## Skipped heading levels

#### A wild h4 appears

Slide headings jumped from h2 to h4 above - screen readers announce
that wrongly. Fix by stepping h2, h3, h4 in order.
