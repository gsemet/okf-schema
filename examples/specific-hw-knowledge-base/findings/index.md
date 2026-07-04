# Finding

A raw, dated, falsifiable observation recorded by an agent or human at a specific point in time. Findings are the atomic unit of empirical knowledge.
Use Finding when you have observed something non-trivial during debugging, investigation, or experimentation and want to preserve that observation for future agents. Do NOT use Finding for stable truths (use Concept), procedures (use Playbook), or human-agreed standards (use Principle).
The body and claim are immutable once written. To correct a Finding, write a new Finding with `contradicts` or `supersedes` pointing to the old one. The only permitted edits to an existing Finding are lifecycle frontmatter: `status` (active, contradicted, superseded), `contradicted_by`, and `superseded_by`, appended by review.
Belongs to the Storage layer. Findings are promoted into Concepts or Structures when they converge and stabilize. They may also support Principles.

- [HW Failure investigation](2026.07.04-21.35-hw-failure-investigation.md) — HW Failure investigation  [Finding]
