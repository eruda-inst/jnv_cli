from typing import TypedDict

TITLE: str = "JNV - Jacobina Network Viewer v1.2.1"

CMD_ONU_ALARMS: str = "O"
CMD_PON_ALARMS: str = "P"

COMMANDS: list[tuple[str, str]] = [
    (CMD_ONU_ALARMS, "Olhar alarmes ONUs"),
    (CMD_PON_ALARMS, "Olhar alarmes da PON"),
]


ONU_DATACOM = TypedDict(
    "ONU_DATACOM",
    {"id": int, "label": str, "serial_number": str, "onu_state": str, "onu_name": str},
)

ONU_FIBERHOME = TypedDict("ONU_FIBERHOME", {"id": int, "label": str, "status": str})


OLTS: dict[str, list[str]] = {
    "OLT ACIJA": [f"SLOT {i:03d}" for i in range(1, 4 + 1)],
    "OLT ITAITU": [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    "OLT JAC 3": [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    "OLT LAJES": [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    "OLT NEWNET": [f"SLOT {i:03d}" for i in range(1, 7 + 1)],
    "OLT PALMEIRINHA": [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    "OLT PARAÍSO": [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
}


def _pons(count: int) -> list[str]:
    return [f"PON {i:03d}" for i in range(1, count + 1)]


OLT_PONS: dict[str, dict[str, list[str]]] = {
    "OLT ACIJA": {slot: _pons(16) for slot in OLTS["OLT ACIJA"]},
    "OLT ITAITU": {slot: _pons(8) for slot in OLTS["OLT ITAITU"]},
    "OLT JAC 3": {slot: _pons(16) for slot in OLTS["OLT JAC 3"]},
    "OLT LAJES": {slot: _pons(16) for slot in OLTS["OLT LAJES"]},
    "OLT NEWNET": {
        **{slot: _pons(8) for slot in OLTS["OLT NEWNET"][:3]},
        **{slot: _pons(16) for slot in OLTS["OLT NEWNET"][3:]},
    },
    "OLT PALMEIRINHA": {slot: _pons(8) for slot in OLTS["OLT PALMEIRINHA"]},
    "OLT PARAÍSO": {slot: _pons(16) for slot in OLTS["OLT PARAÍSO"]},
}
