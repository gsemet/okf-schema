# Image-generation prompt — OKF-KB HW Debugging Overview

## Primary prompt (paste into Nano Banana 2)

A clean hand-drawn systems-engineering overview diagram, horizontal banner layout,
16:6 aspect ratio, white background, sketch-style technical illustration,
dark charcoal pen strokes, handwritten labels, rounded hand-drawn boxes,
clean spacing, highly legible, minimal clutter, architecture-whiteboard aesthetic.

STYLE: Hand-drawn systems architecture sketch on a clean white page,
using black technical-pen strokes, subtle marker highlights, light sketch shading,
slightly imperfect hand-drawn geometry, engineering notebook aesthetic,
similar to Excalidraw drawn by an experienced hardware architect.

The figure is divided into THREE panels separated by faint dashed vertical lines,
each with a bold title at the top.

- LEFT PANEL, titled  **"Debug Sessions".** A vertical stack of five rounded cards, connected
  top-to-bottom by a thin arrow, each card a small note with a tiny microchip icon and a magnifier
  icon. Card labels, top to bottom: "Session 1 · 25°C boot hang", "Session 2 · 0°C thermal sweep",
  "Session 3 · PLL lock measurement", "Session 4 · bootloader source review",
  "Session 5 · fix validated". From EACH session card a thin arrow crosses into the middle panel
  and lands on a distinct small node inside the BLUE base slab of the pyramid, visually showing
  that every session emits one finding at the bottom layer.

- CENTER PANEL, titled  **"OKF-KB Stratified Layers".** A large isometric 3D layered pyramid,
  four stacked translucent slabs. From bottom (widest) to top (narrowest):
    • a pale-BLUE base slab labeled "Findings (raw evidence)", with the sub-caption
      "Immutable · Infalsifiable · Supersedable — what the agent thought at one moment, in one
      context". It holds five glowing finding nodes (one per session), connected to each other by
      thin horizontal dashed links labeled "supersedes / relates_to".
    • a pale-YELLOW slab labeled "Concepts (stable understanding)", with the sub-caption
      "Falsifiable facts, definitions & explanations — revised when new findings contradict them".
    • a pale-CORAL slab labeled "Structures (system patterns)", with the sub-caption
      "Mental model of all concepts — scoped to a domain/team".
    • a pale-PURPLE apex labeled "Principles (team standards)", with the sub-caption
      "Authoritative rules — may be company-wide; human-managed only, never modified by agents".
  Small glowing nodes sit inside each slab, connected by thin vertical "provenance" links.

  On the LEFT of the pyramid, three upward curved arrows show the distillation flow, bottom to top:
    • "record finding" (from the Debug Sessions into the Findings base),
    • "corroborated findings promoted to Concepts" (Findings → Concepts), drawn as a BIDIRECTIONAL
      arrow to convey back-and-forth lineage between concepts and their supporting findings,
    • "consolidate a logical mental model & common definitions" (Concepts → Structures).
  Do NOT draw a distillation arrow into the Principles apex: it stands apart from the automatic
  pipeline (human-governed, not produced by distillation). Mark the Principles slab with a small
  lock icon and a tiny human/person icon to signal it is human-managed only and not fed by the flow.

  On the RIGHT of the pyramid, four small callout file cards float outward with connector lines,
  each showing a snippet of Markdown-with-YAML-frontmatter:
  a purple card "principle.md — Firmware timeouts must be polled",
  a coral card "structure.md — Boot Sequence Architecture",
  a yellow card "concept.md — Boot PLL startup margin (kb_status: active)",
  a blue card "finding.md — PLL lock 200µs→950µs at low temp". Next to the cards, small storage
  icons read "Markdown + Git" (a document icon and a git-branch icon), emphasizing plain-text,
  version-controlled storage. A tiny separate coral card off to the side labeled
  "outcome.md — Fix bootloader PLL polling" hints at a planned deliverable.

- RIGHT PANEL, titled  **"KB Navigation".** At the top, a user avatar with a speech bubble asking
  "Why does boot hang at low temperature?". Below it a row labeled "Navigation Tools" with four
  small pill buttons: "search", "get", "read", "query". Below that, a vertical "agent-guided
  navigation" trace of three connected steps, each a small labeled box with reasoning text:
  step 1 "start at Structures + Concepts (default — findings are NOT read)",
  step 2 "concept 'Boot PLL startup margin' incomplete → drill down into the right up-to-date Findings",
  step 3 "read finding → PLL lock 950µs 400µs wait; cross-check Principle 'timeouts must be
  polled'". The trace ends in a green-outlined answer box: "Bootloader's 400µs PLL wait is too
  short at low temp — poll PLL_LOCK." with a green check-mark badge. A small tag next to the trace
  reads "Findings read only when a concept is incomplete"; a second small tag reads "Principles
  consulted when a new finding appears (company-rule fit)".

Overall look: an academic paper system-overview figure, tidy alignment, generous whitespace,
consistent rounded corners, subtle drop shadows, professional and technical, engineering theme.

---

## Notes for regeneration / tuning

- **Text legibility:** Nano Banana 2 renders short labels best. If any text is garbled, regenerate
  with the offending strings shortened, or generate the figure with placeholder boxes and add the
  final text in a vector editor (Excalidraw / draw.io / Figma).
- **Color = tier semantics (keep consistent with the rest of the docs):**
  blue = Findings, yellow = Concepts, coral = Structures, purple = Principles.
- **Layer semantics (keep exact):**
  - Findings: immutable (only metadata updatable), infalsifiable ("opinion" at a moment/context),
    supersedable (`supersedes` / `superseded_by` / `relates_to`).
  - Concepts: falsifiable definitions & explanations; revised when new findings contradict them;
    bidirectional lineage to findings.
  - Structures: mental model over all concepts; domain/team scope.
  - Principles: authoritative rules, possibly company-wide; NOT produced by distillation and
    **managed only by humans — never modified by agents**.
- **Navigation logic (keep exact):** the agent reads Structures + Concepts by default and does NOT
  read Findings unless a concept is incomplete; Principles are consulted when a new finding appears,
  to check fit with company rules.
- **Storage contrast vs. NapMem:** the original figure shows "vector + json"; OKF-KB is deliberately
  "Markdown + Git" — keep that callout, it is a meaningful design difference.
- **Aspect ratio:** 16:6 wide banner works well in Sphinx `:width: 100%`. A 16:9 variant also works.
- **Palette hex hints (optional):** blue `#CFE3F7`, yellow `#FBF0C4`, coral `#F7CBC5`,
  purple `#E3D4F2`, arrows `#4A4A4A`, background `#FFFFFF`, success green `#3FA34D`.
- **Negative prompt (if supported):** "no photograph, no 3D render noise, no gradients-heavy
  background, no watermark, no lorem ipsum, no distorted text, no overlapping labels".

## Once generated

Reference it from the tutorial with:

    ```{image} ../_static/okfkb-hw-debugging-overview-v2.svg
    :alt: OKF-KB debugging overview — sessions emit findings; distilled into concepts and structures; principles human-governed separately; navigated with search/get/read/query
    :width: 100%
    ```
