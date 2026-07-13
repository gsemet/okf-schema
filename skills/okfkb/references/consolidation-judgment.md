# Consolidation judgment

Consolidation turns episodic Findings into useful stable knowledge without
rewriting history. It is a judgment task, not a vote-counting algorithm.

## Review order

1. Read project rules and schemas.
2. Read recent Findings and their frontmatter first.
3. Search existing Concepts, Structures, Playbooks, Hypotheses, Experiments,
   Outcomes, and Principles that cover the same subject.
4. Build evidence clusters by claim, scope, tags, and relationships.
5. Resolve lifecycle links before proposing new stable documents.
6. Validate every mutation using project-prescribed checks.

## Contradiction versus supersession

Use **contradiction** when claims cannot both hold under materially equivalent
conditions. First test whether differences in version, environment, scope, or
measurement explain the disagreement.

Use **supersession** when a newer record intentionally replaces an older account
or when the old scope is no longer the useful current one. Supersession is not a
way to hide an inconvenient observation.

For both relationships:

- preserve both Finding bodies;
- maintain forward and reciprocal lifecycle fields when schemas allow;
- avoid declaring a winner when evidence is genuinely unresolved;
- create a Hypothesis and Experiment if a targeted test can settle the question.

## Promotion judgment

Promote Findings directly to a Concept or Structure when the agent judges that:

- the evidence converges rather than merely repeats;
- relevant contexts and counter-evidence were considered;
- confidence and source quality are adequate for the claim;
- the synthesis is reusable beyond one incident;
- uncertainty and boundaries can be stated honestly;
- an existing semantic document cannot be updated more cleanly.

No fixed count guarantees promotion. Two strong independent measurements may be
enough; many derivative Findings may not be. Use Hypotheses and Experiments when
evidence remains ambiguous.

Choose **Concept** for the stable idea or explanation and **Structure** for
composition, relationships, architecture, or mechanics. Use schema-canonical
`derived_from` links to preserve provenance.

## Updating stable knowledge

Concepts and Structures are living documents. Update them in place when new
evidence refines the same idea or subject:

- preserve still-valid content;
- revise claims to match the complete evidence;
- add provenance links;
- state important boundaries and unresolved uncertainty;
- add a concise `log.md` entry for material semantic changes.

Deprecate rather than radically repurpose a document when its identity or
subject has changed. Never delete historical semantic documents merely because
they are obsolete.

## Other outputs

- Create a **Hypothesis** for a falsifiable explanation that needs testing.
- Create an **Experiment** for a reusable discriminating procedure; its result
  must be captured as a Finding rather than written into the Experiment body.
- Create or update a **Playbook** when evidence supports a reproducible
  operational workflow.
- Create or update an **Outcome** when the KB identifies a concrete deliverable;
  do not confuse the plan with evidence that it succeeded.
- Propose a **Principle** when evidence suggests a durable normative rule. Give
  the proposed wording, rationale, supporting Findings, and likely impact, but
  do not write or change the Principle without explicit human agreement.

## Quality bar

A consolidation is successful when a future agent can start from stable tiers,
understand what is trusted and why, descend to immutable evidence when needed,
see unresolved disagreement, and avoid re-running settled investigations.