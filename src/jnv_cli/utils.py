import re
from collections.abc import Sequence

NONE_LABEL = "---"
SERIAL_FILTER_SENTINEL = "__SN__"
NO_ALARM_LABEL = "(Sem alarmes)"


def numberfy(value: str | int) -> int:
    return value if isinstance(value, int) else int(value.rsplit(" ", 1)[-1])


def count_alarms_by_filter(
    alarms: Sequence[str], filters: Sequence[tuple[str | None, str]]
) -> dict[str, int]:
    codes = [code for code, _ in filters if code not in (None, SERIAL_FILTER_SENTINEL)]
    count_map = {}

    for code in codes:
        pattern = re.compile(rf"\b{re.escape(code)}\b")
        count_map[code] = sum(1 for line in alarms if pattern.search(line))

    return count_map
