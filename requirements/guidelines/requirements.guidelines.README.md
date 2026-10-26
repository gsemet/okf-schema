# Do not edit `requirements.guidelines.md`

[`requirements.guidelines.md`](requirements.guidelines.md) is generated. It is the guideline that
`okfreq init` installs into every requirements bundle, without the requirement marker of its
source. Any change made here is overwritten by `just refresh-requirements-guideline`, which
preflight runs.

- To change the guideline for every project, edit the original:
  [`src/okf_schema/data/requirements/guidelines/requirements.guidelines.md`](../../src/okf_schema/data/requirements/guidelines/requirements.guidelines.md),
  then run `just refresh-requirements-guideline`.
- To add a rule that only applies to this repository, edit
  [`project.guidelines.md`](project.guidelines.md).
