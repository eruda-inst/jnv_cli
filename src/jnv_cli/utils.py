import logging

from jnv_cli.constants import SEPARATOR

format = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s")
handler = logging.StreamHandler()
logger = logging.getLogger(name=__name__)

handler.setFormatter(fmt=format)
logger.setLevel(level=logging.INFO)
logger.addHandler(hdlr=handler)


def join_values(values: list[str], separator: str = SEPARATOR) -> str:
    return separator.join(map(str, values))


def numberfy(value: str | int) -> int:
    if isinstance(value, int):
        return value
    return int(value.rsplit(" ", 1)[-1])
