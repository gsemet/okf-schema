#!/usr/bin/env python3
"""Deterministic, automated grader for okf-schema skill evals.

Grades agent transcripts against structured assertions from evals.json.
Both with_skill and without_skill conditions use the SAME assertions,
ensuring apples-to-apples comparison for scientific validity.

Usage:
    python grade-eval.py <eval_name> <transcript_path> [--output grading.json]
    python grade-eval.py --all <results_dir>  # Grade all evals in a results/iteration-XXX dir
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def load_evals(evals_path: Path) -> dict:
    """Load evaluation definitions from a JSON file.

    Args:
        evals_path:
            Path to the evaluation definition file.

    Returns:
        Parsed evaluation definitions.
    """
    return json.loads(evals_path.read_text())


def load_transcript(transcript_path: Path) -> str:
    """Load an agent transcript as text.

    Args:
        transcript_path:
            Path to a markdown or plain-text transcript.

    Returns:
        Transcript content, or an empty string when the path does not exist.
    """
    if not transcript_path.exists():
        return ""
    return transcript_path.read_text()


def _normalize_cmd(cmd: str) -> str:
    """Strip uv run prefix, trailing slashes, and normalize --flag=value to --flag value."""
    cmd = cmd.strip()
    if cmd.startswith("uv run -- "):
        cmd = cmd[10:]
    # Normalize --flag=value to --flag value for comparison
    cmd = re.sub(r"(--\w+)=(\S+)", r"\1 \2", cmd)
    # Remove trailing slashes from path-like segments
    parts = cmd.split()
    normalized = []
    for part in parts:
        if part.startswith("skills-evals/") or part.startswith("fixtures/"):
            normalized.append(part.rstrip("/"))
        else:
            normalized.append(part)
    return " ".join(normalized)


def check_command_executed(transcript: str, command: str) -> tuple[bool, str]:
    """Check whether a shell command appears in a transcript.

    Args:
        transcript:
            Transcript text to inspect.
        command:
            Shell command to find after normalization.

    Returns:
        A pass flag and a human-readable explanation.
    """
    target = _normalize_cmd(command)
    # Normalize transcript lines too
    for line in transcript.splitlines():
        line_norm = _normalize_cmd(line)
        if target in line_norm:
            return True, f"Command found: {target[:80]}..."
    return False, f"Command not found: {target[:80]}..."


def check_command_not_executed(transcript: str, command: str) -> tuple[bool, str]:
    """Check that a shell command does NOT appear in executed command lines.

    Unlike ``output_matches`` with a negative-lookahead regex, this only
    inspects lines that look like shell commands (after normalising ``uv run``
    prefixes).  Help output, quoted documentation, and SKILL.md excerpts are
    ignored automatically because they do not contain the full normalised
    command string.

    Args:
        transcript:
            Transcript text to inspect.
        command:
            Shell command that must be absent after normalization.

    Returns:
        A pass flag and a human-readable explanation.
    """
    target = _normalize_cmd(command)
    for line in transcript.splitlines():
        line_norm = _normalize_cmd(line)
        if target in line_norm:
            return False, f"Command was executed: {target[:80]}..."
    return True, f"Command not found: {target[:80]}..."


def check_output_contains(transcript: str, text: str) -> tuple[bool, str]:
    """Check whether a transcript contains text, ignoring case.

    Args:
        transcript:
            Transcript text to inspect.
        text:
            Text to find.

    Returns:
        A pass flag and a human-readable explanation.
    """
    if text.lower() in transcript.lower():
        return True, f"Found: '{text[:60]}...'"
    return False, f"Not found: '{text[:60]}...'"


def check_output_matches(transcript: str, pattern: str) -> tuple[bool, str]:
    """Check whether a transcript matches a regular expression.

    Args:
        transcript:
            Transcript text to inspect.
        pattern:
            Regular expression to search for, ignoring case.

    Returns:
        A pass flag and a human-readable explanation.
    """
    try:
        if re.search(pattern, transcript, re.IGNORECASE):
            return True, f"Pattern matched: {pattern[:60]}..."
        return False, f"Pattern not matched: {pattern[:60]}..."
    except re.error as e:
        return False, f"Invalid regex pattern: {e}"


def check_file_exists(project_dir: Path, rel_path: str) -> tuple[bool, str]:
    """Check whether a project-relative file exists.

    Args:
        project_dir:
            Project root directory.
        rel_path:
            File path relative to the project root.

    Returns:
        A pass flag and a human-readable explanation.
    """
    file_path = project_dir / rel_path
    if file_path.exists():
        return True, f"File exists: {rel_path}"
    return False, f"File not found: {rel_path}"


def check_file_contains(
    project_dir: Path,
    rel_path: str,
    text: str,
) -> tuple[bool, str]:
    """Check whether a project-relative file contains text.

    Args:
        project_dir:
            Project root directory.
        rel_path:
            File path relative to the project root.
        text:
            Text to find, ignoring case.

    Returns:
        A pass flag and a human-readable explanation.

    Examples:
        >>> check_file_contains(Path("."), "README.md", "okf-schema")[0]
        True
    """
    file_path = project_dir / rel_path
    if not file_path.exists():
        return False, f"File not found: {rel_path}"
    content = file_path.read_text()
    if text.lower() in content.lower():
        return True, f"Found '{text[:40]}...' in {rel_path}"
    return False, f"Not found '{text[:40]}...' in {rel_path}"


def check_file_glob_contains(
    project_dir: Path,
    glob_pattern: str,
    text: str,
    exclude: list[str] | None = None,
) -> tuple[bool, str]:
    """Check whether every selected file contains text.

    Args:
        project_dir:
            Project root directory.
        glob_pattern:
            Glob pattern evaluated relative to the project root.
        text:
            Text to find, ignoring case.
        exclude:
            Optional basenames to omit from the check.

    Returns:
        A pass flag and a human-readable explanation.

    Examples:
        >>> check_file_glob_contains(Path("."), "README.md", "okf-schema")[0]
        True
    """
    matches = list(project_dir.glob(glob_pattern))
    if not matches:
        return False, f"No files matched pattern: {glob_pattern}"
    failures = []
    exclude_set = set(exclude or [])
    for fp in matches:
        if fp.name in exclude_set:
            continue
        content = fp.read_text()
        if text.lower() not in content.lower():
            failures.append(fp.name)
    if failures:
        return False, f"Missing '{text}' in: {', '.join(failures)}"
    return True, f"All {len(matches)} files contain '{text[:40]}...'"


def check_file_glob_min_count(
    project_dir: Path,
    glob_pattern: str,
    text: str,
    min_count: int,
    exclude: list[str] | None = None,
) -> tuple[bool, str]:
    """Check whether at least a minimum number of selected files contain text.

    Args:
        project_dir:
            Project root directory.
        glob_pattern:
            Glob pattern evaluated relative to the project root.
        text:
            Text to find, ignoring case.
        min_count:
            Minimum number of matching files required.
        exclude:
            Optional basenames to omit from the check.

    Returns:
        A pass flag and a human-readable explanation.

    Examples:
        >>> check_file_glob_min_count(Path("."), "README.md", "okf-schema", 1)[0]
        True
    """
    matches = list(project_dir.glob(glob_pattern))
    if not matches:
        return False, f"No files matched pattern: {glob_pattern}"
    count = 0
    exclude_set = set(exclude or [])
    for fp in matches:
        if fp.name in exclude_set:
            continue
        content = fp.read_text()
        if text.lower() in content.lower():
            count += 1
    if count >= min_count:
        return True, f"{count} files contain '{text[:40]}...' (min: {min_count})"
    return False, f"Only {count} files contain '{text[:40]}...' (min: {min_count})"


def check_file_glob_max_count(
    project_dir: Path,
    glob_pattern: str,
    text: str,
    max_count: int,
    exclude: list[str] | None = None,
) -> tuple[bool, str]:
    """Check whether at most a maximum number of selected files contain text.

    Args:
        project_dir:
            Project root directory.
        glob_pattern:
            Glob pattern evaluated relative to the project root.
        text:
            Text to find, ignoring case.
        max_count:
            Maximum number of matching files allowed.
        exclude:
            Optional basenames to omit from the check.

    Returns:
        A pass flag and a human-readable explanation.

    Examples:
        >>> check_file_glob_max_count(Path("."), "README.md", "not-present", 0)[0]
        True
    """
    matches = list(project_dir.glob(glob_pattern))
    if not matches:
        return True, f"No files matched pattern: {glob_pattern}"
    count = 0
    exclude_set = set(exclude or [])
    for fp in matches:
        if fp.name in exclude_set:
            continue
        content = fp.read_text()
        if text.lower() in content.lower():
            count += 1
    if count <= max_count:
        return True, f"{count} files contain '{text[:40]}...' (max: {max_count})"
    return False, f"{count} files contain '{text[:40]}...' (exceeds max: {max_count})"


def resolve_placeholders(value: Any, workspace_path: Path | None) -> Any:
    """Replace workspace placeholders in string values.

    Args:
        value:
            Value to process. Non-string values pass through unchanged.
        workspace_path:
            Workspace directory used to resolve placeholders, if available.

    Returns:
        The resolved string, or the original non-string value.
    """
    if not isinstance(value, str):
        return value
    if workspace_path is None:
        return value
    resolved = value.replace("{{workspace}}", str(workspace_path))
    resolved = resolved.replace("{{iteration_dir}}", str(workspace_path.parent.parent.parent))
    return resolved


def grade_assertion(
    assertion: dict,
    transcript: str,
    project_dir: Path,
    workspace_path: Path | None = None,
) -> dict:
    """Grade one assertion against an agent transcript.

    Args:
        assertion:
            Assertion definition, including its check type and target.
        transcript:
            Transcript text to grade.
        project_dir:
            Project root used for file checks.
        workspace_path:
            Optional workspace used to resolve placeholders.

    Returns:
        Structured result containing status and justification.

    Examples:
        >>> assertion = {"text": "mentions OKF", "target": "OKF"}
        >>> grade_assertion(assertion, "OKF bundle", Path("."))["result"]
        'PASS'
    """
    check_type = assertion.get("check", "output_contains")
    target = resolve_placeholders(assertion.get("target", ""), workspace_path)
    params = assertion.get("params", {})
    if params:
        params = {
            k: resolve_placeholders(v, workspace_path) if isinstance(v, str) else v
            for k, v in params.items()
        }

    passed = False
    justification = ""

    if check_type == "command_executed":
        passed, justification = check_command_executed(transcript, target)
    elif check_type == "command_not_executed":
        passed, justification = check_command_not_executed(transcript, target)
    elif check_type == "output_contains":
        passed, justification = check_output_contains(transcript, target)
    elif check_type == "output_matches":
        passed, justification = check_output_matches(transcript, target)
    elif check_type == "file_exists":
        passed, justification = check_file_exists(project_dir, target)
    elif check_type == "file_contains":
        text = params.get("text", "")
        passed, justification = check_file_contains(project_dir, target, text)
    elif check_type == "file_glob_contains":
        glob_pattern = params.get("glob", "")
        text = params.get("text", "")
        exclude = params.get("exclude", [])
        passed, justification = check_file_glob_contains(project_dir, glob_pattern, text, exclude)
    elif check_type == "file_glob_min_count":
        glob_pattern = params.get("glob", "")
        text = params.get("text", "")
        min_count = params.get("min_count", 1)
        exclude = params.get("exclude", [])
        passed, justification = check_file_glob_min_count(
            project_dir, glob_pattern, text, min_count, exclude
        )
    elif check_type == "file_glob_max_count":
        glob_pattern = params.get("glob", "")
        text = params.get("text", "")
        max_count = params.get("max_count", 0)
        exclude = params.get("exclude", [])
        passed, justification = check_file_glob_max_count(
            project_dir, glob_pattern, text, max_count, exclude
        )
    else:
        justification = f"Unknown check type: {check_type}"

    return {
        "assertion": assertion.get("text", "Unnamed assertion"),
        "check_type": check_type,
        "target": target,
        "result": "PASS" if passed else "FAIL",
        "justification": justification,
    }


def grade_eval(
    eval_def: dict,
    transcript: str,
    project_dir: Path,
    workspace_path: Path | None = None,
) -> dict:
    """Grade all assertions for one evaluation case.

    Args:
        eval_def:
            Evaluation definition containing assertions and metadata.
        transcript:
            Transcript text to grade.
        project_dir:
            Project root used for file checks.
        workspace_path:
            Optional workspace used to resolve placeholders.

    Returns:
        Evaluation summary and individual assertion results.

    Examples:
        >>> definition = {"id": 1, "assertions": []}
        >>> grade_eval(definition, "", Path("."))["overall"]
        'PASS'
    """
    results = []
    for assertion in eval_def.get("assertions", []):
        result = grade_assertion(assertion, transcript, project_dir, workspace_path)
        result["tier"] = assertion.get("tier", "secondary")
        results.append(result)

    passed = sum(1 for r in results if r["result"] == "PASS")
    total = len(results)

    primary_results = [r for r in results if r.get("tier") == "primary"]
    primary_passed = sum(1 for r in primary_results if r["result"] == "PASS")
    primary_total = len(primary_results)

    return {
        "eval_id": eval_def.get("id"),
        "eval_name": eval_def.get("eval_name"),
        "overall": "PASS" if passed == total else "PARTIAL" if passed > 0 else "FAIL",
        "pass_rate": passed / total if total else 0.0,
        "primary_pass_rate": primary_passed / primary_total if primary_total else 0.0,
        "primary_passed": primary_passed,
        "primary_total": primary_total,
        "passed": passed,
        "failed": total - passed,
        "total": total,
        "assertions": results,
        "notes": eval_def.get("notes", ""),
    }


def grade_iteration(
    iteration_dir: Path,
    evals_path: Path,
    project_dir: Path,
) -> list[dict]:
    """Grade both conditions for every evaluation in an iteration.

    Args:
        iteration_dir:
            Directory containing evaluation condition transcripts.
        evals_path:
            Path to the JSON evaluation definitions.
        project_dir:
            Project root used for file checks and relative output paths.

    Returns:
        Results for every condition that has a transcript.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as tmp:
        ...     root = Path(tmp)
        ...     evals_path = root / "evals.json"
        ...     _ = evals_path.write_text('{"evals": []}', encoding="utf-8")
        ...     grade_iteration(root / "iteration", evals_path, root)
        []
    """
    evals = load_evals(evals_path)
    all_results = []

    for eval_def in evals.get("evals", []):
        eval_name = eval_def["eval_name"]
        eval_dir = iteration_dir / eval_name

        for condition in ["with_skill", "without_skill"]:
            transcript_path = eval_dir / condition / "transcript.md"
            output_path = eval_dir / condition / "grading.json"

            transcript = load_transcript(transcript_path)
            if not transcript:
                print(f"  ⚠️  No transcript for {eval_name}/{condition}, skipping")
                continue

            # Resolve workspace path from eval definition
            workspace_raw = eval_def.get("workspace", "")
            if workspace_raw:
                workspace_path = Path(
                    workspace_raw.replace("{{iteration_dir}}", str(iteration_dir)).replace(
                        "{{condition}}", condition
                    )
                )
            else:
                workspace_path = None

            result = grade_eval(eval_def, transcript, project_dir, workspace_path)
            result["condition"] = condition
            result["transcript_path"] = str(transcript_path.relative_to(project_dir))

            output_path.write_text(json.dumps(result, indent=2))
            print(f"  ✅ Graded {eval_name}/{condition}: {result['passed']}/{result['total']}")
            all_results.append(result)

    return all_results


def main() -> None:
    """Parse command-line arguments and run the requested grading mode."""
    parser = argparse.ArgumentParser(description="Deterministic grader for okf-schema evals")
    parser.add_argument("--evals", "-e", type=Path, default=Path("skills-evals/evals.json"))
    parser.add_argument("--project-dir", "-p", type=Path, default=Path("."))
    parser.add_argument("--iteration", "-i", type=Path, help="Grade all evals in iteration dir")
    parser.add_argument("--eval", type=str, help="Single eval name to grade")
    parser.add_argument("--transcript", "-t", type=Path, help="Transcript file path")
    parser.add_argument("--output", "-o", type=Path, default=Path("grading.json"))
    args = parser.parse_args()

    if args.iteration:
        print(f"=== Grading iteration: {args.iteration.name} ===")
        results = grade_iteration(args.iteration, args.evals, args.project_dir)
        print(f"\nGraded {len(results)} condition-eval pairs.")
        return

    if not args.eval or not args.transcript:
        parser.print_help()
        sys.exit(1)

    evals = load_evals(args.evals)
    eval_def = next((e for e in evals.get("evals", []) if e["eval_name"] == args.eval), None)
    if not eval_def:
        print(f"Error: Eval '{args.eval}' not found in {args.evals}", file=sys.stderr)
        sys.exit(1)

    transcript = load_transcript(args.transcript)
    result = grade_eval(eval_def, transcript, args.project_dir)
    args.output.write_text(json.dumps(result, indent=2))
    print(f"Graded {result['passed']}/{result['total']} — written to {args.output}")


if __name__ == "__main__":
    main()
