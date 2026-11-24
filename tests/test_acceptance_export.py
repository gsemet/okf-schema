"""Run the checked-in example's acceptance tests from the project suite.

The acceptance test itself lives beside the example, in
``examples/okfreq-examples/tests/test_acceptance_export.py``: its
``@accepts_req StRS-CORE-001#S1`` marker has to be scanned inside the example
project, where ``accepted_in_files`` reports it as
``tests/test_acceptance_export.py``. This module only delegates to it, so the
example's acceptance evidence also runs in ``just test``.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

EXAMPLE_TEST = (
    Path(__file__).parents[1] / "examples/okfreq-examples/tests/test_acceptance_export.py"
)


def _example_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("okfreq_example_acceptance", EXAMPLE_TEST)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fast_export_selected_rows_for_offline_review(tmp_path: Path) -> None:
    """The example's main path S1 runs as the user does, in a separate process."""
    _example_module().test_fast_export_selected_rows_for_offline_review(tmp_path)


def test_commented_marker_does_not_count(tmp_path: Path) -> None:
    """The commented slow variant is not evidence; without the fast marker W004 returns."""
    _example_module().test_commented_marker_does_not_count(tmp_path)
