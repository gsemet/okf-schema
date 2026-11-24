"""Export tabular rows for the ``okfreq`` traceability example.

The example deliberately uses the standard-library CSV writer and fixes line
endings to ``\n`` so generated output is identical on every platform.
"""

import csv
import io
import json
import sys
from pathlib import Path


# @implements_req SwRS-CORE-001
def export_rows(rows: list[list[str]]) -> str:
    r"""Return rows as comma-separated values (CSV) with Unix line endings.

    Args:
        rows:
            String-valued rows to serialize.

    Returns:
        CSV text terminated with ``\n`` for each row.

    Examples:
        >>> export_rows([["name", "value"], ["alpha", "1"]])
        'name,value\nalpha,1\n'
    """
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue()


def main() -> None:
    """Export a JSON list of rows to a CSV file."""
    if len(sys.argv) != 3:
        raise SystemExit("usage: export.py <rows.json> <report.csv>")
    rows = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    Path(sys.argv[2]).write_text(export_rows(rows), encoding="utf-8")


if __name__ == "__main__":
    main()
