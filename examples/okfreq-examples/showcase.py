"""Run concrete okfreq scenarios in a disposable project.

Run from the repository root with ``uv run python
examples/okfreq-examples/showcase.py``. The checked-in CSV example is preserved;
all configuration, lifecycle changes and intentional failures stay temporary.
Its markers are linkage fixtures: the checked-in example's executable evidence is
``tests/test_export.py`` and its acceptance test ``tests/test_acceptance_export.py``.
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from click.testing import CliRunner
from jsonschema import Draft202012Validator

from okf_schema._internal.yaml import dump_yaml, extract_frontmatter, make_yaml
from okf_schema.file_links import inspect_file_links
from okf_schema.okfreq.cli import okfreq
from okf_schema.okfreq.core import (
    load_requirements,
    report,
    report_schema,
    validate_requirements,
)
from okf_schema.projection import LINKS_START, strip_links_section

# @implements_req SwRS-OKFSCHEMA-OKFREQ-008


def run_showcase(project: Path) -> dict[str, str]:
    """Exercise authoring, evidence, reports, navigation and recovery scenarios.

    Args:
        project:
            An empty disposable project directory owned by this example.

    Returns:
        Scenario names with their verified outcomes.
    """
    project.mkdir(parents=True, exist_ok=True)
    runner = CliRunner()
    outcomes: dict[str, str] = {}

    def command(*args: str, expected: int = 0) -> str:
        result = runner.invoke(okfreq, list(args))
        assert result.exit_code == expected, (args, result.output, result.exception)
        return result.output

    def edit(path: Path, updates: dict) -> None:
        text = path.read_text(encoding="utf-8")
        frontmatter, body = extract_frontmatter(text)
        data = make_yaml().load(frontmatter)
        for key, value in updates.items():
            if value is None:
                data.pop(key, None)
            else:
                data[key] = value
        path.write_text(f"---\n{dump_yaml(data)}---\n{body}", encoding="utf-8")

    root = project / "requirements"
    command("init", str(root))
    config_path = root / "config.yml"
    config = make_yaml().load(config_path.read_text(encoding="utf-8"))
    config["scopes"] = {
        "delivery": {
            "id_token": "DELIVERY",
            "folder": "delivery",
            "source_dirs": ["src"],
            "test_dirs": ["tests"],
        }
    }
    config["markers"]["implements"] = "@delivers"
    config["markers"]["tests"] = "@verifies"
    config["strs_test_coverage_mode"] = "linked-swrs-and-validation-test"
    config_path.write_text(dump_yaml(config), encoding="utf-8")
    common = ["--path", str(root), "--scope", "delivery", "--project", "shipping"]
    command(
        "new",
        "strs",
        "Export shipping manifest",
        *common,
        "--description",
        "The dispatch team SHALL receive a portable shipping manifest.",
        "--user-need",
        "Dispatchers need to review shipments offline.",
    )
    parent = "StRS-DELIVERY-001"
    for title in ("Write a manifest", "Format a replacement manifest"):
        command(
            "new",
            "swrs",
            title,
            *common,
            "--description",
            "When export is requested, the service SHALL return manifest CSV.",
            "--derives-from",
            parent,
        )
    swrs = "SwRS-DELIVERY-001"
    replacement = "SwRS-DELIVERY-002"
    records = load_requirements(root)
    edit(
        records[swrs][0],
        {
            "depends_on": [replacement],
            "external_id": "DEMO-4821",
            "external_url": "https://example.com/tracker/DEMO-4821",
            "owner": "dispatch",
            "verification_method": "test",
            "verification_criteria": "The returned manifest preserves populated and empty rows.",
        },
    )
    for folder in ("src", "tests"):
        (project / folder).mkdir()
    (project / "src/manifest.py").write_text(
        f"# @delivers {swrs}\n# @delivers {replacement}\n", encoding="utf-8"
    )
    test_path = project / "tests/test_manifest.py"
    test_path.write_text(f"# @verifies {swrs}\n# @verifies {replacement}\n", encoding="utf-8")
    before = report(root)
    assert before["stakeholder_test_coverage"]["covered"] == 0
    test_path.write_text(test_path.read_text() + f"# @verifies {parent}\n", encoding="utf-8")
    assert report(root)["stakeholder_test_coverage"]["covered"] == 1
    outcomes["strict_stakeholder_coverage"] = (
        "requires linked SwRS tests and a direct validation test"
    )

    # Acceptance paths: the StRS declares its main paths, the SwRS its transitions,
    # and each test marker names one with a #S<n> fragment.
    earlier_mode = config["strs_test_coverage_mode"]
    earlier_tests = test_path.read_text(encoding="utf-8")
    strs_file = records[parent][0]
    strs_file.write_text(
        strs_file.read_text(encoding="utf-8").replace(
            "### Preserved stakeholder intent",
            "### Main paths\n\n#### Path 1: Pick ready shipments\n\n"
            "1. The dispatcher selects the ready shipments.\n"
            "2. The manifest lists them for offline review.\n\n"
            "#### Path 2: Replace a sent manifest\n\n"
            "1. The dispatcher corrects a sent shipment.\n"
            "2. A replacement manifest lists the corrected shipment.\n\n"
            "### Preserved stakeholder intent",
            1,
        ),
        encoding="utf-8",
    )
    config["markers"]["accepts"] = "@accepts"
    config["strs_test_coverage_mode"] = "linked-swrs-and-acceptance-paths"
    config_path.write_text(dump_yaml(config), encoding="utf-8")

    def strs_coverage() -> dict:
        by_id = {record["id"]: record for record in report(root)["requirements"]}
        return by_id[parent]["stakeholder_test_coverage"]

    def write_tests(*markers: str) -> list[str]:
        test_path.write_text("".join(f"# {marker}\n" for marker in markers), encoding="utf-8")
        return validate_requirements(root)

    findings = validate_requirements(root)
    w003 = next(item for item in findings if item.startswith("W003") and parent in item)
    assert '"Path 1: Pick ready shipments"; "Path 2: Replace a sent manifest"' in w003
    assert "- id: S1\n  title: Pick ready shipments\n- id: S2\n" in w003
    assert any(item.startswith("W004") and parent in item for item in findings)
    scenarios = [{"id": "S1", "title": "Nominal manifest"}, {"id": "S2", "title": "Replacement"}]
    edit(strs_file, {"scenarios": [{**item} for item in scenarios]})
    edit(records[swrs][0], {"scenarios": [{**item} for item in scenarios]})
    findings = validate_requirements(root)
    assert not any(item.startswith("W003") for item in findings)
    for line, target in ((1, swrs), (3, parent)):
        assert any(
            item.startswith(f"tests/test_manifest.py:{line}: @verifies {target} has no scenario")
            for item in findings
        ), findings
    assert not any(f"@verifies {replacement}" in item for item in findings)
    tests_status = {
        record["id"]: record["tests"]["status"] for record in report(root)["requirements"]
    }
    assert tests_status[swrs] == "missing" and tests_status[replacement] == "covered"
    assert strs_coverage()["paths"]["tested"] == 0
    findings = write_tests(f"@verifies {swrs}#S9")
    assert any(f"@verifies {swrs}#S9 names no declared scenario" in item for item in findings)
    markers = [f"@verifies {replacement}", f"@accepts {parent}#S1"]
    findings = write_tests(*markers)
    assert not any(item.startswith("W004") for item in findings)
    coverage = strs_coverage()
    assert coverage["paths"] == {"total": 2, "tested": 0, "accepted": 1}
    assert (coverage["tested"], coverage["accepted"], coverage["status"]) == (
        False,
        False,
        "missing",
    )
    markers += [f"@verifies {parent}#S1", f"@verifies {parent}#S2"]
    write_tests(*markers)
    coverage = strs_coverage()
    assert coverage["paths"] == {"total": 2, "tested": 2, "accepted": 1}
    assert (coverage["tested"], coverage["accepted"]) == (True, False)
    markers.append(f"@accepts {parent}#S2")
    write_tests(*markers)
    coverage = strs_coverage()
    assert coverage["paths"] == {"total": 2, "tested": 2, "accepted": 2}
    assert (coverage["accepted"], coverage["status"]) == (True, "missing")
    markers.append(f"@verifies {swrs}#S1")
    write_tests(*markers)
    assert strs_coverage()["linked_swrs"][0] == {"id": swrs, "status": "missing"}
    markers.append(f"@verifies {swrs}#S2")
    write_tests(*markers)
    assert strs_coverage()["status"] == "covered"
    findings = write_tests(*markers, f"@accepts {swrs}")
    assert any(
        item.startswith(f"tests/test_manifest.py:{len(markers) + 1}: @accepts {swrs}: Never")
        for item in findings
    ), findings
    Draft202012Validator(report_schema()).validate(report(root))
    outcomes["acceptance_paths"] = (
        "main paths accepted and tested apart; fragments checked; W003/W004 guide the author"
    )
    config["strs_test_coverage_mode"] = earlier_mode
    config_path.write_text(dump_yaml(config), encoding="utf-8")
    test_path.write_text(earlier_tests, encoding="utf-8")

    config["strs_test_coverage_mode"] = "linked-swrs"
    config_path.write_text(dump_yaml(config), encoding="utf-8")
    test_path.write_text(f"# @verifies {swrs}\n# @verifies {replacement}\n", encoding="utf-8")
    assert report(root)["stakeholder_test_coverage"]["covered"] == 1
    config["strs_test_coverage_mode"] = "linked-swrs-and-validation-test"
    config_path.write_text(dump_yaml(config), encoding="utf-8")
    test_path.write_text(test_path.read_text() + f"# @verifies {parent}\n", encoding="utf-8")
    # These markers demonstrate linkage only. Actual CSV behavior is tested in
    # tests/test_export.py in the checked-in example, and its acceptance test is
    # tests/test_acceptance_export.py; this fixture claims neither.
    preserved = load_requirements(root)[swrs][1]
    command("update-coverage", str(root), "--diff")
    command("update-coverage", str(root))
    command("update-coverage", str(root), "--check")
    assert load_requirements(root)[swrs][1]["owner"] == preserved["owner"]
    command("validate", str(root), "--check-links", "--project-root", str(project))
    for operation in ("index", "status", "scope", "graph", "trace"):
        command(operation, str(root))
    assert swrs in command("search", "manifest", str(root))
    command("in-file", str(records[swrs][0]))
    outcomes["authoring_and_navigation"] = (
        "scoped IDs, dependencies and external metadata preserved"
    )
    outcomes["custom_markers_and_scopes"] = (
        "source/test markers resolve through explicit project roots"
    )

    incoming = project / "incoming.yml"
    incoming.write_text("version: 99\nproducer: demo-import\n", encoding="utf-8")
    command("config-merge", str(incoming), "--path", str(root))
    merged = make_yaml().load(config_path.read_text(encoding="utf-8"))
    assert merged["version"] == 1 and merged["producer"] == "demo-import"
    outcomes["config_merge"] = "destination conflicts retained; unknown keys imported"

    destination = project / "dist/requirements-report.json"
    destination.parent.mkdir()
    command(
        "generate-report",
        str(root),
        "--output-json",
        str(destination),
        "--output-summary-md",
        str(destination.with_suffix(".md")),
    )
    payload = json.loads(destination.read_text())
    schema = json.loads(destination.with_suffix(".schema.json").read_text())
    Draft202012Validator(schema).validate(payload)
    assert payload["execution_evidence"]["status"] == "not_collected"
    outcomes["reports"] = (
        "JSON validates against emitted schema; Markdown emitted; execution unclaimed"
    )

    def link(mode: str, syntax: str = "plain") -> dict:
        return {"type": "string", "x-okf-link": {"resolution": mode, "syntax": syntax}}

    path = records[swrs][0]
    relative = path.relative_to(root).as_posix()
    schema = {
        "properties": {
            "document": link("document-relative"),
            "bundle": link("bundle-relative"),
            "stem_path": link("bundle-relative-stem"),
            "source": link("project-relative"),
            "wiki": link("filename-stem", "wikilink"),
        }
    }
    values = {
        "document": path.name,
        "bundle": relative,
        "stem_path": relative[:-3],
        "source": "src/manifest.py",
        "wiki": f"[[{parent}#User Need|Dispatch need]]",
    }
    results = inspect_file_links(values, schema, path, bundle_root=root, project_root=project)
    assert len(results) == 5 and all(r.status == "valid" for r in results)
    values["source"] = "src/missing.py"
    assert any(
        r.code == "E10"
        for r in inspect_file_links(values, schema, path, bundle_root=root, project_root=project)
    )
    unavailable = inspect_file_links({"bundle": relative}, schema, path)
    assert unavailable[0].code == "W15"
    outcomes["five_file_resolutions"] = (
        "plain/wikilink targets resolved; missing and skipped checks separated"
    )

    body_before = extract_frontmatter(path.read_text())[1]
    edit(
        path,
        {
            "annotation_exemption": True,
            "exemption_reason": "Demonstration of external verification policy.",
        },
    )
    assert any(item["id"] == swrs for item in report(root)["marker_coverage"]["exemptions"])
    command("archive", swrs, "--path", str(root), expected=1)
    command("archive", swrs, "--path", str(root), "--yes")
    assert load_requirements(root)[swrs][1]["req_lifecycle"] == "deprecated"
    assert load_requirements(root)[swrs][1]["status"] == "deprecated"
    command("supersede", swrs, replacement, "--path", str(root), "--yes")
    after = load_requirements(root)[swrs]
    assert after[1]["superseded_by"] == [replacement]
    assert strip_links_section(extract_frontmatter(after[2])[1]) == strip_links_section(body_before)
    assert f"- Superseded by:\n  - [{replacement}]" in after[2]
    assert after[1]["uuid"] == records[swrs][1]["uuid"]
    outcomes["exemptions_and_lifecycle"] = (
        "explicit exemption, confirmation, supersession and stable UUID/body"
    )

    draft_args = ("new", "swrs", "Discarded draft", *common, "--derives-from", parent)
    draft_args += ("--description", "When asked, the service SHALL write a draft.")
    command(*draft_args)
    draft = "SwRS-DELIVERY-003"
    command("retire", draft, "--path", str(root), expected=1)
    command("retire", replacement, "--path", str(root), "--yes", expected=1)
    command("retire", draft, "--path", str(root), "--reason", "Merged", "--yes")
    assert draft not in load_requirements(root)
    assert draft in config_path.read_text(encoding="utf-8")
    assert "SwRS-DELIVERY-004.md" in command(*draft_args)
    outcomes["retired_ids_are_never_reused"] = (
        "referenced or unconfirmed retirement refused; the retired number is skipped"
    )

    second_replacement = "SwRS-DELIVERY-004"
    command("supersede", swrs, replacement, second_replacement, "--path", str(root), "--yes")
    assert load_requirements(root)[swrs][1]["superseded_by"] == [replacement, second_replacement]
    assert "supersedes" not in load_requirements(root)[replacement][1]
    command("update-coverage", str(root), "--check", expected=1)
    command("update-coverage", str(root))
    command("update-coverage", str(root), "--check")
    for successor in (replacement, second_replacement):
        assert load_requirements(root)[successor][1]["supersedes"] == [swrs]
    edit(records[swrs][0].parent / f"{replacement}.md", {"relates_to": [second_replacement]})
    graph_result = json.loads(command("graph", str(root), "--json"))
    assert graph_result["relates_to"][replacement] == [second_replacement]
    assert graph_result["supersedes"][second_replacement] == [swrs]
    assert any(record["supersedes"] == [swrs] for record in report(root)["requirements"])
    command("supersede", replacement, swrs, "--path", str(root), "--yes", expected=1)
    unreplaced = records[swrs][0].parent / f"{second_replacement}.md"
    edit(unreplaced, {"req_lifecycle": "superseded"})
    assert "requires a non-empty superseded_by" in command(
        "validate", str(root), "--json", expected=1
    )
    edit(unreplaced, {"req_lifecycle": "draft"})
    command("validate", str(root))
    outcomes["supersession_and_relations"] = (
        "several replacements, generated supersedes, relates_to; cycles and gaps refused"
    )

    config = make_yaml().load(config_path.read_text(encoding="utf-8"))
    config["tiers"]["StRS"]["owner_email"] = "product-owner@example.org"
    config_path.write_text(dump_yaml(config), encoding="utf-8")
    command("update-coverage", str(root))
    owned = records[parent][0]
    assert load_requirements(root)[parent][1]["default_owner_email"] == "product-owner@example.org"
    edit(owned, {"req_lifecycle": "approved"})
    refusal = command("validate", str(root), "--json", expected=1)
    assert "requires approved_by and approved_at" in refusal
    assert "request the owner's review" in refusal
    assert "status draft does not match req_lifecycle approved" in refusal
    edit(
        owned,
        {"approved_by": "product-owner@example.org", "approved_at": "2026-10-28T09:00:00+01:00"},
    )
    command("update-coverage", str(root))
    command("validate", str(root))
    approved = load_requirements(root)[parent]
    assert approved[1]["status"] == "stable"
    assert approved[1]["verified"] == {
        "by": "human:product-owner@example.org",
        "at": "2026-10-28T09:00:00+01:00",
    }
    assert LINKS_START in approved[2] and f"- Derived by:\n  - [{swrs}]" in approved[2]
    unlockable = records[swrs][0].parent / f"{replacement}.md"
    edit(unlockable, {"req_lifecycle": "approved", "approved_by": "a@example.org"})
    assert "approval_lock is false" in command("validate", str(root), "--json", expected=1)
    edit(unlockable, {"req_lifecycle": "proposed", "approved_by": None})
    command("update-coverage", str(root))
    command("validate", str(root))
    outcomes["ownership_and_approval"] = (
        "owner generated from the tier; approval needs the owner's recorded agreement and a lock"
    )
    outcomes["okf_projection"] = (
        "status, human verified event and Links sections generated for plain OKF consumers"
    )

    broken = root / "tiers/strs/broken.md"
    broken.write_text("---\ntype: StRS\n---\nNo ID\n", encoding="utf-8")
    assert "broken.md" in command("validate", str(root), expected=1)
    broken.unlink()
    command("lint", str(root), "--check-links", "--project-root", str(project))
    command("lint", str(root), "--check")
    assert (root / "tiers/swrs/delivery/index.md").is_file()
    assert "SwRS-DELIVERY-001.md" in (root / "tiers/swrs/delivery/index.md").read_text()
    outcomes["invalid_document_recovery"] = (
        "missing ID fails explicitly; repair restores validation"
    )
    return outcomes


if __name__ == "__main__":
    with TemporaryDirectory(prefix="okfreq-showcase-") as directory:
        print(json.dumps(run_showcase(Path(directory)), indent=2))
