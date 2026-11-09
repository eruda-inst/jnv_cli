# import logging

from jnv_cli.constants import SEPARATOR

# format = "%(asctime)s - %(levelname)s - %(message)s"
# logging.basicConfig(format=format, level=logging.DEBUG)
# logger = logging.getLogger(name=__name__)


def join_values(values: list[str], separator: str = SEPARATOR) -> str:
    return separator.join(map(str, values))


def numberfy(value: str | int) -> int:
    if isinstance(value, int):
        return value
    return int(value.rsplit(" ", 1)[-1])
