# Playbook

A reproducible, step-by-step workflow or procedure that produces a specific result given the current understanding of the system.
Use Playbook when documenting "how to do X" — deployment steps, debugging procedures, setup guides. Do NOT use Playbook for one-off observations (use Finding), system architecture (use Structure), or planned deliverables (use Outcome).
Mutable while active. When a better workflow is found, the old Playbook is marked `kb_status: deprecated` or `superseded` with `superseded_by` pointing to the replacement. Playbooks are experienced until proven false or obsolete.
Belongs to the Operational layer. References Concepts and Structures for context. May be referenced by Outcomes as execution paths.

- [Investigate recurring hardware failures](investigate-recurring-hardware-failures.md) — Reproduce and isolate a hardware failure signature without losing the original test boundary.  [Playbook]
