from jnv_cli.constants import SEPARATOR


def join_values(values: list[str], separator: str = SEPARATOR) -> str:
    return separator.join(map(str, values))
