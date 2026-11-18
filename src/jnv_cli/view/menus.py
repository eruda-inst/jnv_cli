from collections.abc import Sequence

from jnv_cli.types.onu import ONUDatacom, ONUFiberhome
from jnv_cli.utils import NONE_LABEL, SERIAL_FILTER_SENTINEL

_COLUMN_SEPARATOR = " | "


def _join_values(values: list[str], separator: str = " | ") -> str:
    return separator.join(map(str, values))


def build_filter_labels(
    count_map: dict[str, int],
    filters: Sequence[tuple[str | None, str]],
    total: int,
) -> tuple[str, list[str]]:
    rows: list[list[str]] = []
    for order, (code, label) in enumerate(filters, start=1):
        if code is None:
            code_text = NONE_LABEL
            count_text = f"{total:03d}"
        elif code == SERIAL_FILTER_SENTINEL:
            code_text = NONE_LABEL
            count_text = NONE_LABEL
        else:
            code_text = code
            count_text = f"{count_map[code]:03d}"
        rows.append([f"{order:03d}", code_text, label, count_text])

    columns = ["ORDER", "CODE", "LABEL", "COUNT"]
    return _format_table(columns, rows)


def _build_onu_rows(
    onus: Sequence[ONUDatacom | ONUFiberhome],
) -> tuple[list[str], list[list[str]]]:
    is_datacom = isinstance(onus[0], ONUDatacom)

    if is_datacom:
        columns = ["ORDER", "ID", "SERIAL", "OST", "NAME"]
    else:
        columns = ["ORDER", "ID", "SERIAL", "OST", "STATUS"]

    rows: list[list[str]] = []
    for order, onu in enumerate(onus, start=1):
        last = onu.name if is_datacom else onu.status  # type: ignore
        rows.append([f"{order:03d}", f"{onu.id:03d}", onu.serial, onu.ost, last])

    return columns, rows


def _format_table(columns: list[str], rows: list[list[str]]) -> tuple[str, list[str]]:
    widths = [len(column) for column in columns]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(value))

    def format_row(values: list[str]) -> str:
        return _COLUMN_SEPARATOR.join(
            value if i == len(values) - 1 else value.ljust(widths[i])
            for i, value in enumerate(values)
        )

    header = format_row(columns)
    labels = [format_row(row) for row in rows]
    return header, labels


def build_onu_menu(
    onus: Sequence[ONUDatacom | ONUFiberhome],
) -> tuple[str, list[str]]:
    if not onus:
        return "", []

    columns, rows = _build_onu_rows(onus)
    return _format_table(columns, rows)


def build_order_menu(
    labels: Sequence[str],
    column: str = "OLT",
    strip_prefix: str | None = None,
) -> tuple[str, list[str]]:
    if not labels:
        return "", []

    columns = ["ORDER", column]
    rows: list[list[str]] = []
    for order, label in enumerate(labels, start=1):
        display = label.removeprefix(strip_prefix) if strip_prefix else label
        rows.append([f"{order:03d}", display])

    return _format_table(columns, rows)
