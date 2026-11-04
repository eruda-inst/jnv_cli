from jnv_cli.constants import SEPARATOR


def join_values(values: list[str], separator: str = SEPARATOR) -> str:
    return separator.join(map(str, values))


def numberfy(value: str | int) -> int:
    if isinstance(value, int):
        return value
    return int(value.rsplit(" ", 1)[-1])
