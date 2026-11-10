TITLE = "JNV (Jacobina Network Viewer) v1.11.1"
CREDITS = "Desenvolvido pelo setor de inovação da Newnet"
COMMANDS = ("Consultar alarmes das ONUs", "Consultar alarmes da PON")
SEPARATOR = " | "
NONE_SUBSTITUTE = "---"
SERIAL_FILTER_SENTINEL = "__SN__"
DATACOM_ALARM_FILTER_CODES = (
    None,
    SERIAL_FILTER_SENTINEL,
    "GPON_DGi",
    "GPON_LOSi",
    "GPON_DFi",
    "GPON_DOWi",
    "GPON_LCDGi",
    "GPON_LOAi",
    "GPON_LOAMi",
    "GPON_LOBi",
    "GPON_LOFi",
    "GPON_LOOCi",
    "GPON_LOPCi",
    "GPON_MISi",
    "GPON_ONU_AUTO_PROV_FAIL",
    "GPON_ONU_DOWN",
    "GPON_ONU_EQUIP_FAILURE",
    "GPON_ONU_PASSWORD_MISMATCH",
    "GPON_ONU_SELF_TEST_FAILURE",
    "GPON_PEEi",
    "GPON_RDIi",
    "GPON_SDi",
    "GPON_SFi",
    "GPON_SUFi",
)
DATACOM_ALARM_FILTER_LABELS = (
    "Todas",
    "Digite o serial number da ONU",
    "ONUs com perda de energia (Dying Gasp)",
    "ONUs com perda de sinal (LOS)",
    "ONUs com falha de desativação (DFi)",
    "ONUs com deslocamento da janela (DOWi)",
    "ONUs com perda do delineamento do canal GEM (LCDGi)",
    "ONUs com perda de reconhecimento (LOAi)",
    "ONUs com perda de PLOAM (LOAMi)",
    "ONUs com perda de rajada (LOBi)",
    "ONUs com perda de frame (LOFi)",
    "ONUs com perda do canal OMCC (LOOCi)",
    "ONUs com perda do canal PLOAM (LOPCi)",
    "ONUs com incompatibilidade de link (MISi)",
    "ONUs com falha no provisionamento automático",
    "ONUs inativas ou desconectadas do link PON",
    "ONUs com falha interna/defeito de equipamento",
    "ONUs com incompatibilidade de senha",
    "ONUs com falha no autoteste",
    "ONUs com erro de equipamento físico (PEEi)",
    "ONUs com indicação remota de defeito (RDIi)",
    "ONUs com sinal degradado (SDi)",
    "ONUs com falha de sinal (SFi)",
    "ONUs com falha de inicialização (SUFi)",
)
DATACOM_ALARM_FILTERS = [
    (DATACOM_ALARM_FILTER_CODES[i], DATACOM_ALARM_FILTER_LABELS[i])
    for i in range(len(DATACOM_ALARM_FILTER_LABELS))
]
FIBERHOME_ALARM_FILTER_CODES = (
    None,
    SERIAL_FILTER_SENTINEL,
    "active",
    "inactive",
    "link loss",
    "power down",
)
FIBERHOME_ALARM_FILTER_LABELS = (
    "Todas",
    "Digite o serial number da ONU",
    "ONUs sem alarmes",
    "ONUs inativas (LOS ou Dying Gasp)",
    "ONUs com perda de sinal (LOS)",
    "ONUs com perda de energia (Dying Gasp)",
)
FIBERHOME_ALARM_FILTERS = [
    (FIBERHOME_ALARM_FILTER_CODES[i], FIBERHOME_ALARM_FILTER_LABELS[i])
    for i in range(len(FIBERHOME_ALARM_FILTER_LABELS))
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
OLT_PONS = {
    "OLT de Acija": {
        slot: [f"PON {i:03d}" for i in range(1, 16 + 1)]
        for slot in OLTS["OLT de Acija"]
    },
    "OLT de Itaitú": {
        slot: [f"PON {i:03d}" for i in range(1, 8 + 1)]
        for slot in OLTS["OLT de Itaitú"]
    },
    "OLT de Jacobina III": {
        slot: [f"PON {i:03d}" for i in range(1, 16 + 1)]
        for slot in OLTS["OLT de Jacobina III"]
    },
    "OLT de Lajes do Batata": {
        slot: [f"PON {i:03d}" for i in range(1, 16 + 1)]
        for slot in OLTS["OLT de Lajes do Batata"]
    },
    "OLT de Newnet": {
        **{
            slot: [f"PON {i:03d}" for i in range(1, 8 + 1)]
            for slot in OLTS["OLT de Newnet"][:3]
        },
        **{
            slot: [f"PON {i:03d}" for i in range(1, 16 + 1)]
            for slot in OLTS["OLT de Newnet"][3:]
        },
    },
    "OLT de Palmeirinha": {
        slot: [f"PON {i:03d}" for i in range(1, 8 + 1)]
        for slot in OLTS["OLT de Palmeirinha"]
    },
    "OLT de Paraíso": {
        slot: [f"PON {i:03d}" for i in range(1, 16 + 1)]
        for slot in OLTS["OLT de Paraíso"]
    },
}
