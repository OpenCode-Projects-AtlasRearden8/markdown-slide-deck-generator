# Split By Headings

This deck demonstrates `--split headings`. Run it with:

    python3 mdslide.py examples/split-headings.md --split headings

Every `#` and `##` heading starts a new slide, so plain outlines
become decks without any `---` rules in sight.

# One main heading starts a slide

## and a subheading starts another

Because `--heading-level` defaults to 2, both the `#` above and this
`##` kicked off their own slides.

### h3 does NOT start a slide

h3 and below stay *inside* the current slide, so you can subdivide
freely.

# Another main heading

Tip: use `--heading-level 1` when subheadings belong on the same
slide as their parent.
