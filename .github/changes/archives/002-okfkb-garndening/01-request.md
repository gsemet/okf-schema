# OKFKB Gardening

need a skill to "upkeep" an OKFKB bundle (the opinionated one)

first and most important role: links quality

- correct links (files might have been moved, renamed, or deleted)
- ensure `okfkb update` pass
- cleverly trigger subagent to verify coherencies of each links (need to use a smaller model like Haiky or Kimi K2.7)
- find obsolete or superseeded findings and correct them
- links to findings that became obsolete or superseeded should be removed ; every removed links have the equivalent to a non-obsolete finding or concept.

At the end, a coherency report can be presented to the user to highlight any important issue,
like contradicting information, missing context.

For instance, we are on a project called SDV, we have building SW for automotive.
We have 53 "systems" (brake control, steering, etc.) and each system will have
its own set of findings.

This was for a project called "26.2". Now we are switching to 28.2, another version of
this ecosystem, where we will have only 31 systems. So, there is a "contextual" information
to provide to each findings so the agent can instantanously find if it is relevant for the
given SW it is working on at this time.

There can be several other "up-most important" context like this I cannot give now.

---

if you think you will need to update the okf-schema CLI (especially adding subcommands to `okfkb`),
propose your options.
