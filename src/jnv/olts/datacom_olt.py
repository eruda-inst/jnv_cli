import re
from typing import ClassVar, TypedDict

from ..clients.ssh_client import SSHClient
from ..config import settings


class ONUDatacom(TypedDict):
    id: int
    label: str
    serial_number: str
    onu_state: str
    onu_name: str


class DatacomOLT:
    OLT_SSH_HOSTNAMES: ClassVar[dict[str, str]] = {
        "OLT ITAITU": settings.olt_itaitu_hostname,
        "OLT JAC 3": settings.olt_jac_3_hostname,
        "OLT LAJES": settings.olt_lajes_hostname,
        "OLT PALMEIRINHA": settings.olt_palmeirinha_hostname,
        "OLT PARAÍSO": settings.olt_paraiso_hostname,
    }

    def __init__(self, ssh_client: SSHClient) -> None:
        self.ssh_client = ssh_client

    @staticmethod
    def _numberfy(value: str | int) -> int:
        if isinstance(value, int):
            return value
        return int(value.rsplit(" ", 1)[-1])

    def _run_ssh(self, command: str) -> list[str]:
        self.ssh_client.execute_command(command=command)
        stdout = self.ssh_client.get_stdout()
        return stdout.splitlines() or ["(Sem alarmes)"]

    @classmethod
    def is_ssh_olt(cls, olt: str) -> bool:
        return olt in cls.OLT_SSH_HOSTNAMES

    def get_onus(
        self, slot: str = "SLOT 001", pon: str = "PON 001"
    ) -> list[ONUDatacom]:
        slot_number = self._numberfy(value=slot)
        pon_number = self._numberfy(value=pon)
        command = f"show interface gpon 1/{slot_number}/{pon_number} onu"
        lines = self._run_ssh(command=command)
        lines = lines[2:]

        onus: list[ONUDatacom] = []

        for line in lines:
            onu_id = int(line.split()[1])
            onu_serial_number = line.split()[2]
            onu_state = line.split()[3]
            onu_state = onu_state.ljust(4)

            onu_name = "---"

            if len(line.split()) >= 6:
                onu_name = line.split()[5]

            onus.append(
                ONUDatacom(
                    id=onu_id + 1,
                    label=f"ONU {onu_id:03d}",
                    serial_number=onu_serial_number,
                    onu_state=onu_state,
                    onu_name=onu_name,
                )
            )

        return onus

    def get_onu_ids_with_alarm(
        self, alarm_lines: list[str], alarm_code: str
    ) -> set[int]:
        onu_ids: set[int] = set()

        code_re = re.compile(rf"\b{re.escape(alarm_code)}\b")
        gpon_interface_re = re.compile(r"gpon-\d+/\d+/\d+/(\d+)")

        for line in alarm_lines:
            if not code_re.search(line):
                continue
            match = gpon_interface_re.search(line)
            if match:
                onu_ids.add(int(match.group(1)))

        return onu_ids

    def run_onu_alarms(self, pon: str = "PON 001", onu: str = "PON 001") -> list[str]:
        pon_number = self._numberfy(value=pon)
        onu_number = self._numberfy(value=onu) - 1
        command = f'show alarm | include "gpon-1/1/{pon_number}/{onu_number} "'
        return self._run_ssh(command=command)

    def run_pon_alarms(self, pon: str = "PON 001") -> list[str]:
        pon_number = self._numberfy(value=pon)
        return self._run_ssh(command=f"show alarm | include 1/1/{pon_number}/")
