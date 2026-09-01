feat(skills): install packaged agent skills by family

Users can install the packaged `okf-schema`, `okfkb`, and `okfreq`
skills into an agent skills directory through the matching command, from
the installed Python wheel.

Each entry point uses the same destination selectors and precedence rules,
while family-scoped staging, status reporting, safe replacement, and
symlink rejection keep unrelated project content intact.

Assisted-by: Claude:Opus-4.7 Craftsman
