# Interview Responses — okf-schema Project

## Round 1

**Q1: Package name and purpose**
> okf-schema

**Q2: License**
> MIT

**Q3: Build backend**
> hatchling

**Q4: Linting tools**
> ruff

**Q5: Stop the interview here?**
> No, continue

---

## Round 2

**Q6: Library purpose**
> validate okf bundle + optionally validate against a jsonschema. the code is already in skills/Engineering/Knowledge_Graphs/okf/scripts/validate_schema.py

**Q7: CLI entry point**
> okf-schema

**Q8: CI/CD platform**
> GitHub Actions

**Q9: Documentation**
> Sphinx

**Q10: Stop the interview here?**
> No, continue

---

## Round 3

**Q11: CLI structure**
> One command with subcommands

**Q12: Python API**
> Both CLI and API

**Q13: Type checker**
> ty

**Q14: Coverage target**
> 95%

**Q15: Stop the interview here?**
> No, continue

---

## Round 4

**Q13 (clarify): Type checker**
> https://github.com/astral-sh/ty

**Q16: Pre-commit hooks**
> No

**Q17: Test framework**
> pytest

**Q18: Task runner**
> just

**Q19: Stop the interview here?**
> No, continue

---

## Round 5

**Q20: Package layout**
> src/ layout

**Q21: PyPI publishing**
> Trusted publishing (OIDC)

**Q22: Extra files**
> CONTRIBUTING.md, .editorconfig

**Q23: Code origin**
> Adapted/refactored into clean package

**Q24: Stop the interview here?**
> No, continue

---

## Round 6

**Q25: Dependencies**
> no idea. i need a formatter subcommand that will ensure the lists in the frontmatter are flat AND it does not break existing comments. in the validate command also support unflatten list check with recommendation how to fix it

**Q26: Versioning**
> Automatic from git tags (hatch-vcs)

**Q27: Author info**
> Gaetan Semet

**Q28: Additional features**
> the formatter i told you

**Q29: Stop the interview here?**
> No, continue

---

## Round 7

**Q30: Author email**
> gaetan@xeberon.net

**Q31: Formatter behavior**
> In-place (like black without args)

**Q32: Unflatten list check**
> Error (non-conformant)

**Q33: Formatter as subcommand**
> Separate subcommand: okf-schema format

**Q34: Stop the interview here?**
> No, continue

---

## Round 8

**Q35: GitHub repo URL**
> https://github.com/gsemet/okf-schema (already checked out in /Users/az02065/Projects/DevTools/okf-schema)

**Q36: Subcommands**
> add these:
> - init — Initialize a new OKF bundle
> - new — Create a new concept interactively
> - validate — Validate bundle structure and frontmatter
> - list — List all concepts in the bundle
> - show — Display a single concept
> - index — Auto-generate index.md files
> - search — Full-text search across concepts
> - graph — Output the concept link graph
> - stats — Bundle statistics

**Q37: PyPI description**
> Open Knowledge Format with JSONSchema

**Q38: PyPI keywords**
> ok

**Q39: Stop the interview here?**
> No, continue

---

## Round 9

**Q40: MVP scope**
> part of the initial plan. also add a skill in the skills folder

**Q41: init subcommand**
> create folder, bundle root index, root log, that's all. Beware the schema folder shall NOT be in the bundle. for instance `okf-schema init kb` you will create a folder 'kb/bundle' (with index and log) and kb/schema

**Q42: new subcommand**
> yes. 2 parameters: '--path' path to the root (the path with schema and bundle underneath). second parameter is --name the relative path ('concepts/ideas')

**Q43: index subcommand**
> it regenerates the index.md files in the bundle

**Q44: Stop the interview here?**
> No, continue

---

## Round 10

**Q45: Skill details**
> add a skills folder inside your new project. this skill will 'teach' agent on how to use okf-schema

**Q46: graph subcommand**
> for the moment only ASCII output. later i will want one or more output files (html, json,...)

**Q47: search subcommand**
> Frontmatter only

**Q48: stats subcommand**
> here is an example. use only for inspiration.
>
> ```
> okf stats /Users/az02065/Projects/Nestor/moulinsart/memory-bank
>
> Bundle Statistics
>   Bundle root:    /Users/az02065/Projects/Nestor/moulinsart/memory-bank
>   Total files:     23
>   Concepts:        16
>   No frontmatter:  0
>   Total size:      46.3 KB
>
>   By Type:
>     Deployment Pattern           2  ██
>     Cluster Reference            2  ██
>     Troubleshooting Guide        2  ██
>     Playbook                     1  █
>     Storage Strategy             1  █
>     Reference                    1  █
>     Overlay Pattern              1  █
>     Storage Reference            1  █
>     Registry Reference           1  █
>     Network Configuration        1  █
>     Registry Strategy            1  █
>     Operations Guide             1  █
>     Lifecycle Playbook           1  █
>
>   Tags Cloud:
>     k8s      16  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
>     nestor   16  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
>
>   Links:            3 total, 0 broken
> ```

**Q49: Stop the interview here?**
> No, continue

---

## Round 11

**Q50: Project skill content**
> Yes, Compendium-style SKILL.md

**Q51: OKF schema files**
> 2 user provided, but source tree contains documentation with example in json and yaml (both following JSONSchema)

**Q52: Docs setup**
> API + CLI reference

**Q53: GitHub Actions**
> use a single `just` command to trigger all checks, and publish in a second job

**Q54: Stop the interview here?**
> No, continue

---

## Round 12

**Q55: Just command name**
> just preflight

**Q56: Schema examples**
> Both

**Q57: Default schema**
> Yes, built-in minimal schema

**Q58: Bundle structure**
> yes.

**Q59: Stop the interview here?**
> Yes, stop
