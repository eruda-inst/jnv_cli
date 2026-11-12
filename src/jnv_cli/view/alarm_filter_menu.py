from collections.abc import Sequence

from jnv_cli.utils import SERIAL_FILTER_SENTINEL, join_values

"""
# DATACOM
def get_filter_count_map(self, pon: str = "PON 001") -> dict[str, int]:
    def get_filter_count(alarms: list[str], filter: str) -> int:
        return len([alarm for alarm in alarms if filter == alarm])

    raw_lines = self.get_pon_alarms(pon=pon)
    alarms = []
    filter_count_map = {}

    for raw_line in raw_lines:
        line = raw_line.strip()
        parts = line.split()
        status = parts[2]
        alarms.append(status)

    for code in DATACOM_ALARM_FILTER_CODES[2::]:
        filter_count_map[code] = get_filter_count(alarms=alarms, filter=code)

    return filter_count_map

# FIBERHOME
@staticmethod
def get_filter_count_map(onus: list[ONUFiberhome]) -> dict[str, int]:
    def get_filter_count(onus: list[ONUFiberhome], filter: str) -> int:
        return len([onu for onu in onus if onu.status == filter])

    filter_count_map = {}
    for code in FIBERHOME_ALARM_FILTER_CODES[2::]:
        filter_count_map[code] = get_filter_count(onus=onus, filter=code)

    return filter_count_map
"""


def build_filter_labels(
    count_map: dict[str, int], filters: Sequence[tuple[str | None, str]]
) -> list[str]:
    max_code = max(len(c) for c, _ in filters[2::])  # type: ignore
    max_label = max(len(l) for _, l in filters[2::])

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
