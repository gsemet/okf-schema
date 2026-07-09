# Image-generation prompt — OKF-KB HW Debugging Overview

## Primary prompt (paste into Nano Banana 2)

> A clean, modern academic infographic diagram, horizontal banner layout, 16:6 aspect ratio,
> flat vector illustration style, soft pastel color palette (pale blue, pale yellow, pale
> coral/pink, pale purple), thin rounded rectangles, thin dark-grey arrows, white background,
> crisp legible sans-serif labels, no photorealism, no clutter. The figure is divided into THREE
> panels separated by faint dashed vertical lines, each with a bold title at the top.
>
> **LEFT PANEL, titled "Debug Sessions".** A vertical stack of five rounded cards, connected
> top-to-bottom by a thin arrow, each card a small note with a tiny microchip icon and a magnifier
> icon. Card labels, top to bottom: "Day 1 · 25°C boot hang", "Day 2 · 0°C thermal sweep",
> "Day 3 · PLL lock measurement", "Day 5 · bootloader source review", "Day 15 · fix validated".
> A large arrow points from this panel into the middle panel.
>
> **CENTER PANEL, titled "OKF-KB Stratified Layers".** A large isometric 3D layered pyramid,
> four stacked translucent slabs. From bottom (widest) to top (narrowest): a pale-BLUE base slab
> labeled "Findings (raw evidence)", a pale-YELLOW slab labeled "Concepts (stable understanding)",
> a pale-CORAL slab labeled "Structures (system patterns)", and a pale-PURPLE apex labeled
> "Principles (team standards)". Small glowing nodes sit inside each slab, connected by thin
> vertical "provenance" links between layers. On the LEFT of the pyramid, three upward curved
> arrows are labeled, bottom to top: "record finding", "promote on convergence", "team consensus".
> On the RIGHT of the pyramid, four small callout file cards float outward with connector lines,
> each showing a snippet of Markdown-with-YAML-frontmatter:
> a purple card "principle.md — Firmware timeouts must be polled",
> a coral card "structure.md — Boot Sequence Architecture",
> a yellow card "concept.md — Boot PLL startup margin (status: resolved)",
> a blue card "finding.md — PLL lock 200µs→950µs at low temp". Next to the cards, small storage
> icons read "Markdown + Git" (a document icon and a git-branch icon), emphasizing plain-text,
> version-controlled storage. A tiny separate coral card off to the side labeled
> "outcome.md — Fix bootloader PLL polling" hints at a planned deliverable.
>
> **RIGHT PANEL, titled "KB Navigation".** At the top, a user avatar with a speech bubble asking
> "Why does boot hang at low temperature?". Below it a row labeled "Navigation Tools" with four
> small pill buttons: "search", "get", "read", "query". Below that, a vertical "agent-guided
> navigation" trace of three connected steps, each a small labeled box with reasoning text:
> step 1 "read principles → Firmware Timeouts Must Be Polled",
> step 2 "query: finding[tag=pll] -> concept -> principle",
> step 3 "get finding → PLL lock 950µs > 400µs wait". The trace ends in a green-outlined answer
> box: "Bootloader's 400µs PLL wait is too short at low temp — poll PLL_LOCK." with a green
> check-mark badge. A small "stop when sufficient" tag sits next to the final step.
>
> Overall look: an academic paper system-overview figure, tidy alignment, generous whitespace,
> consistent rounded corners, subtle drop shadows, professional and technical, engineering theme.

---

## Notes for regeneration / tuning

- **Text legibility:** Nano Banana 2 renders short labels best. If any text is garbled, regenerate
  with the offending strings shortened, or generate the figure with placeholder boxes and add the
  final text in a vector editor (Excalidraw / draw.io / Figma).
- **Color = tier semantics (keep consistent with the rest of the docs):**
  blue = Findings, yellow = Concepts, coral = Structures, purple = Principles.
- **Storage contrast vs. NapMem:** the original figure shows "vector + json"; OKF-KB is deliberately
  "Markdown + Git" — keep that callout, it is a meaningful design difference.
- **Aspect ratio:** 16:6 wide banner works well in Sphinx `:width: 100%`. A 16:9 variant also works.
- **Palette hex hints (optional):** blue `#CFE3F7`, yellow `#FBF0C4`, coral `#F7CBC5`,
  purple `#E3D4F2`, arrows `#4A4A4A`, background `#FFFFFF`, success green `#3FA34D`.
- **Negative prompt (if supported):** "no photograph, no 3D render noise, no gradients-heavy
  background, no watermark, no lorem ipsum, no distorted text, no overlapping labels".

## Once generated

Reference it from the tutorial with:

```markdown
```{image} ../_static/okfkb-hw-debugging-overview.png
:alt: OKF-KB debugging overview — debug sessions feed a stratified pyramid (findings → concepts → structures → principles), navigated with search/get/read/query
:width: 100%
```
```
