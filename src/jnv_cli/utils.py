NONE_SUBSTITUTE = "---"
SERIAL_FILTER_SENTINEL = "__SN__"


def join_values(values: list[str], separator: str = " | ") -> str:
    return separator.join(map(str, values))


def numberfy(value: str | int) -> int:
    if isinstance(value, int):
        return value
    return int(value.rsplit(" ", 1)[-1])
