from collections.abc import Sequence

NONE_LABEL = "---"
SERIAL_FILTER_SENTINEL = "__SN__"
NO_ALARM_LABEL = "(Sem alarmes)"


def join_values(values: list[str], separator: str = " | ") -> str:
    return separator.join(map(str, values))


def numberfy(value: str | int) -> int:
    if isinstance(value, int):
        return value
    return int(value.rsplit(" ", 1)[-1])


def count_alarms_by_filter(
    alarms: Sequence[str], filters: Sequence[tuple[str | None, str]]
) -> dict[str, int]:
    codes = [code for code, _ in filters if code not in (None, SERIAL_FILTER_SENTINEL)]
    raw_lines = alarms
    count_map = {}

    for code in codes:
        count_map[code] = 0
        for raw_line in raw_lines:
            line = raw_line.strip()
            if code in line:
                count_map[code] = count_map[code] + 1

    return count_map
