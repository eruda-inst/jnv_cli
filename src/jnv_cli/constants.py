TITLE = "JNV (Jacobina Network Viewer) v1.5.3"
CREDITS = "Desenvolvido pelo setor de inovação da Newnet"

COMMANDS = ("Consultar alarmes das ONUs", "Consultar alarmes da PON")

ALARM_FILTERS = [
    (None, "Todas as ONUs"),
    ("GPON_DGi", "ONUs com perda de energia (Dying Gasp)"),
    ("GPON_LOSi", "ONUs com perda de sinal (LOS)"),
    ("GPON_LOFi", "ONUs com perda de quadro (LOF)"),
    ("GPON_LOAMi", "ONUs com perda de PLOAM (PLOAM Loss)"),
]

ALARM_FILTERS_FIBERHOME = [
    (None, "Todas as ONUs"),
    ("Active", "ONUs sem alarmes"),
    ("Inactive", "ONUs inativas (LOS ou Dying Gasp)"),
    ("Link loss", "ONUs com perda de sinal (LOS)"),
    ("Power down", "ONUs com perda de energia (Dying Gasp)"),
]


OLTS = {
    "OLT de Acija": [f"SLOT {i:03d}" for i in range(1, 4 + 1)],
    "OLT de Itaitú": [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    "OLT de Jacobina III": [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    "OLT de Lajes do Batata": [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    "OLT de Newnet": [f"SLOT {i:03d}" for i in range(1, 7 + 1)],
    "OLT de Palmeirinha": [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    "OLT de Paraíso": [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
}


def _pons(count: int) -> list[str]:
    return [f"PON {i:03d}" for i in range(1, count + 1)]


OLT_PONS = {
    "OLT de Acija": {slot: _pons(16) for slot in OLTS["OLT de Acija"]},
    "OLT de Itaitú": {slot: _pons(8) for slot in OLTS["OLT de Itaitú"]},
    "OLT de Jacobina III": {slot: _pons(16) for slot in OLTS["OLT de Jacobina III"]},
    "OLT de Lajes do Batata": {
        slot: _pons(16) for slot in OLTS["OLT de Lajes do Batata"]
    },
    "OLT de Newnet": {
        **{slot: _pons(8) for slot in OLTS["OLT de Newnet"][:3]},
        **{slot: _pons(16) for slot in OLTS["OLT de Newnet"][3:]},
    },
    "OLT de Palmeirinha": {slot: _pons(8) for slot in OLTS["OLT de Palmeirinha"]},
    "OLT de Paraíso": {slot: _pons(16) for slot in OLTS["OLT de Paraíso"]},
}
