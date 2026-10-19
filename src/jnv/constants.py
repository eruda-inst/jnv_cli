from typing import TypedDict

TITLE: str = "JNV - Jacobina Network Viewer v1.0.2"

CMD_ONU_ALARMS: str = "O"
CMD_PON_ALARMS: str = "P"

COMMANDS: list[tuple[str, str]] = [
    (CMD_ONU_ALARMS, "Olhar alarmes ONUs"),
    (CMD_PON_ALARMS, "Olhar alarmes da PON"),
]


ONU = TypedDict("ONU", {"id": int, "label": str})


OLTS: dict[str, list[str]] = {
    "OLT ACIJA": [f"SLOT {i:03d}" for i in range(1, 4 + 1)],
    "OLT ITAITU": [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    "OLT JAC 3": [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    "OLT LAJES": [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    "OLT NEWNET": [f"SLOT {i:03d}" for i in range(1, 7 + 1)],
    "OLT PALMEIRINHA": [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    "OLT PARAÍSO": [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
}
