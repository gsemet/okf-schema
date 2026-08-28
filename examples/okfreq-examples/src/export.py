"""Small implementation used by the okfreq traceability example."""

import csv
import io


# @implements_req SwRS-default-001
def export_rows(rows: list[list[str]]) -> str:
    """Return *rows* as CSV with stable Unix line endings."""
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue()
