"""Export tabular rows for the ``okfreq`` traceability example.

The example deliberately uses the standard-library CSV writer and fixes line
endings to ``\n`` so generated output is identical on every platform. Run
``python src/export.py <rows.json> <report.csv>`` to export a JSON list of rows.
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


def main(argv: list[str]) -> None:
    """Write the rows of a JSON file to a CSV report.

    Args:
        argv:
            The JSON rows file and the CSV report path.
    """
    rows_path, report_path = argv
    rows = json.loads(Path(rows_path).read_text(encoding="utf-8"))
    Path(report_path).write_text(export_rows(rows), encoding="utf-8", newline="")


if __name__ == "__main__":
    main(sys.argv[1:])
