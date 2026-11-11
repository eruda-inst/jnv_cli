import re
from dataclasses import dataclass
from typing import ClassVar

from jnv_cli.clients.ssh_client import SSHClient
from jnv_cli.config import settings
from jnv_cli.constants import NONE_SUBSTITUTE
from jnv_cli.utils import join_values, numberfy


@dataclass
class ONUDatacom:
    id: int
    label: str
    status: str
    serial_number: str
    name: str


class DatacomOLT:
    ONU_RE: ClassVar[re.Pattern[str]] = re.compile(
        pattern=r"\d+/\d+/\d+\s+\d+\s+\w{12}\s+(Up|Down)\s+\w+\s{0,}\S{0,}"
    )
    GPON_RE: ClassVar[re.Pattern[str]] = re.compile(pattern=r"gpon-\d+/\d+/\d+/(\d+)")
    DATACOM_HOSTNAMES: ClassVar[dict[str, str]] = {
        "OLT de Itaitú": settings.olt_itaitu_hostname,
        "OLT de Jacobina III": settings.olt_jac_3_hostname,
        "OLT de Lajes do Batata": settings.olt_lajes_hostname,
        "OLT de Palmeirinha": settings.olt_palmeirinha_hostname,
        "OLT de Paraíso": settings.olt_paraiso_hostname,
    }

    def __init__(self, ssh_client: SSHClient) -> None:
        self.ssh_client = ssh_client

    def _run_command(self, command: str) -> list[str]:
        self.ssh_client.execute_command(command=command)
        stdout = self.ssh_client.get_stdout()
        return stdout.splitlines() or ["(Sem alarmes)"]

    @classmethod
    def is_datacom_olt(cls, olt: str) -> bool:
        return olt in cls.DATACOM_HOSTNAMES

    def get_onu_label(self, onu: ONUDatacom) -> str:
        onu_label = onu.label
        onu_serial_number = onu.serial_number
        status = onu.status
        name = onu.name
        return join_values(values=[onu_label, onu_serial_number, status, name])

    def get_onus(self, pon: str = "PON 001") -> list[ONUDatacom]:
        pon_number = numberfy(value=pon)
        command = f"show interface gpon 1/1/{pon_number} onu"

        raw_lines = self._run_command(command=command)
        onus = []

        for raw_line in raw_lines:
            line = raw_line.strip()
            match = self.ONU_RE.search(string=line)

            if match is not None:
                result_raw = match.group()
                result = result_raw.strip()

                parts = result.split()

                onu_id = int(parts[1])
                onu_serial_number = parts[2]
                status = parts[3].ljust(4)
                name = NONE_SUBSTITUTE

                if len(parts) >= 6:
                    name = parts[5]

                onus.append(
                    ONUDatacom(
                        id=onu_id + 1,
                        label=f"ONU {onu_id:03d}",
                        serial_number=onu_serial_number,
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
            match = self.GPON_RE.search(string=line)
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
