import re
from typing import ClassVar

from jnv_cli.clients.ssh_client import SSHClient
from jnv_cli.config import settings
from jnv_cli.types.olt_names import OLTNames
from jnv_cli.types.onu import ONUDatacom
from jnv_cli.utils import NONE_SUBSTITUTE, SERIAL_FILTER_SENTINEL, join_values, numberfy

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


class DatacomOLT:
    _ONU_RE: ClassVar[re.Pattern[str]] = re.compile(
        pattern=r"\d+/\d+/\d+\s+\d+\s+\w{12}\s+(Up|Down)\s+\w+\s{0,}\S{0,}"
    )
    _GPON_RE: ClassVar[re.Pattern[str]] = re.compile(pattern=r"gpon-\d+/\d+/\d+/(\d+)")
    DATACOM_HOSTNAMES: ClassVar[dict[OLTNames, str]] = {
        OLTNames.ITAITU: settings.olt_itaitu_hostname,
        OLTNames.JACOBINA_III: settings.olt_jac_3_hostname,
        OLTNames.LAGES_DO_BATATA: settings.olt_lajes_hostname,
        OLTNames.PALMEIRINHA: settings.olt_palmeirinha_hostname,
        OLTNames.PARAISO: settings.olt_paraiso_hostname,
    }

    def __init__(self, ssh_client: SSHClient) -> None:
        self.client = ssh_client

    def _run_command(self, command: str) -> list[str]:
        self.client.execute_command(command=command)
        stdout = self.client.get_stdout()
        return stdout.splitlines() or ["(Sem alarmes)"]

    def get_filter_count_map(self, pon: str = "PON 001") -> dict[str, int]:
        def get_filter_count(alarms: list[str], filter: str) -> int:
            return len([alarm for alarm in alarms if filter == alarm])

        raw_lines = self.get_pon_alarms(pon=pon)
        alarms = []
        filter_count_map = {}

        for raw_line in raw_lines:
            line = raw_line.strip()
            if line:
                parts = line.split()
                status = parts[6]
                alarms.append(status)

        for code in DATACOM_ALARM_FILTER_CODES[2::]:
            filter_count_map[code] = get_filter_count(alarms=alarms, filter=code)

        return filter_count_map

    @classmethod
    def is_datacom_olt(cls, olt: str) -> bool:
        return olt in cls.DATACOM_HOSTNAMES

    def get_onu_label(self, onu: ONUDatacom) -> str:
        return join_values(values=[onu.label, onu.serial, onu.status, onu.name])

    def get_onus(self, pon: str = "PON 001") -> list[ONUDatacom]:
        pon_number = numberfy(value=pon)
        command = f"show interface gpon 1/1/{pon_number} onu"

        raw_lines = self._run_command(command=command)
        onus = []

        for raw_line in raw_lines:
            line = raw_line.strip()
            match = self._ONU_RE.search(string=line)

            if match is not None:
                result_raw = match.group()
                result = result_raw.strip()

                parts = result.split()

                onu_id = int(parts[1])
                onu_serial = parts[2]
                status = parts[3].ljust(4)
                name = NONE_SUBSTITUTE

                if len(parts) >= 6:
                    name = parts[5]

                onus.append(
                    ONUDatacom(
                        id=onu_id + 1,
                        label=f"ONU {onu_id:03d}",
                        serial=onu_serial,
                        status=status,
                        name=name,
                    )
                )

        return onus

    def get_onu_ids_with_alarm(
        self, alarm_lines: list[str], alarm_code: str
    ) -> set[int]:
        onu_ids: set[int] = set()
        code_re = re.compile(rf"\b{re.escape(alarm_code)}\b")

        for line in alarm_lines:
            if not code_re.search(string=line):
                continue
            match = self._GPON_RE.search(string=line)
            if match:
                onu_ids.add(int(match.group(1)))

        return onu_ids

    def get_onu_alarms(self, pon: str = "PON 001", onu: str = "ONU 000") -> list[str]:
        pon_number = numberfy(value=pon)
        onu_number = numberfy(value=onu) - 1
        command = f'show alarm | include "gpon-1/1/{pon_number}/{onu_number} "'
        return self._run_command(command=command)

    def get_pon_alarms(self, pon: str = "PON 001") -> list[str]:
        pon_number = numberfy(value=pon)
        command = f"show alarm | include 1/1/{pon_number}/"
        return self._run_command(command=command)
