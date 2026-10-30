TITLE = "JNV (Jacobina Network Viewer) v1.7.3"
CREDITS = "Desenvolvido pelo setor de inovação da Newnet"

COMMANDS = ("Consultar alarmes das ONUs", "Consultar alarmes da PON")

SERIAL_FILTER_SENTINEL = "__SN__"

ALARM_FILTERS = [
    (None, "Todas as ONUs"),
    (SERIAL_FILTER_SENTINEL, "Digite o serial number da ONU"),
    ("GPON_DGi", "ONUs com perda de energia (Dying Gasp)"),
    ("GPON_LOSi", "ONUs com perda de sinal (LOS)"),
    ("GPON_DFi", "ONUs com falha de desativação (DFi)"),
    ("GPON_DOWi", "ONUs com deslocamento da janela (DOWi)"),
    ("GPON_LCDGi", "ONUs com perda do delineamento do canal GEM (LCDGi)"),
    ("GPON_LOAi", "ONUs com perda de reconhecimento (LOAi)"),
    ("GPON_LOAMi", "ONUs com perda de PLOAM (LOAMi)"),
    ("GPON_LOBi", "ONUs com perda de rajada (LOBi)"),
    ("GPON_LOFi", "ONUs com perda de frame (LOFi)"),
    ("GPON_LOOCi", "ONUs com perda do canal OMCC (LOOCi)"),
    ("GPON_LOPCi", "ONUs com perda do canal PLOAM (LOPCi)"),
    ("GPON_MISi", "ONUs com incompatibilidade de link (MISi)"),
    ("GPON_ONU_AUTO_PROV_FAIL", "ONUs com falha no provisionamento automático"),
    ("GPON_ONU_DOWN", "ONUs inativas ou desconectadas do link PON"),
    ("GPON_ONU_EQUIP_FAILURE", "ONUs com falha interna/defeito de equipamento"),
    ("GPON_ONU_PASSWORD_MISMATCH", "ONUs com incompatibilidade de senha"),
    ("GPON_ONU_SELF_TEST_FAILURE", "ONUs com falha no autoteste"),
    ("GPON_PEEi", "ONUs com erro de equipamento físico (PEEi)"),
    ("GPON_RDIi", "ONUs com indicação remota de defeito (RDIi)"),
    ("GPON_SDi", "ONUs com sinal degradado (SDi)"),
    ("GPON_SFi", "ONUs com falha de sinal (SFi)"),
    ("GPON_SUFi", "ONUs com falha de inicialização (SUFi)"),
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
