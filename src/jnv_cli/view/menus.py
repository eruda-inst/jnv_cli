from collections.abc import Sequence

from jnv_cli.types.onu import ONUDatacom, ONUFiberhome
from jnv_cli.utils import SERIAL_FILTER_SENTINEL, join_values


def build_filter_labels(
    count_map: dict[str, int], filters: Sequence[tuple[str | None, str]]
) -> list[str]:
    max_code = max(
        len(code) for code, _ in filters if code not in (None, SERIAL_FILTER_SENTINEL)
    )
    max_label = max(
        len(label)
        for _, label in filters
        if label not in (None, SERIAL_FILTER_SENTINEL)
    )
    return [
        label
        if code in (None, SERIAL_FILTER_SENTINEL)
        else join_values(
            values=[
                code.ljust(max_code),
                label.ljust(max_label),
                f"{count_map[code]:03d}",
            ]
        )
        for code, label in filters
    ]


def build_onu_labels(onu: ONUDatacom | ONUFiberhome) -> str:
    if isinstance(onu, ONUDatacom):
        return join_values(values=[onu.label, onu.serial, onu.ost, onu.name])
    elif isinstance(onu, ONUFiberhome):
        return join_values(values=[onu.label, onu.serial, onu.ost, onu.status])
