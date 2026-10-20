from typing import ClassVar

from .. import clients, config, constants


class DatacomOLT:
    NON_SSH_OLTS: ClassVar[frozenset[str]] = frozenset({"OLT ACIJA", "OLT NEWNET"})

    OLT_SSH_HOSTNAMES: ClassVar[dict[str, str]] = {
        "OLT ITAITU": config.settings.olt_itaitu_hostname,
        "OLT JAC 3": config.settings.olt_jac_3_hostname,
        "OLT LAJES": config.settings.olt_lajes_hostname,
        "OLT PALMEIRINHA": config.settings.olt_palmeirinha_hostname,
        "OLT PARAÍSO": config.settings.olt_paraiso_hostname,
    }

    def __init__(self, ssh_client: clients.SSHClient) -> None:
        self.ssh_client = ssh_client

    @staticmethod
    def _onu_number(onu: int | str) -> str:
        if isinstance(onu, str):
            raw = onu.rsplit(" ", 1)[-1]
            try:
                return str(int(raw))
            except ValueError:
                return raw
        return str(onu)

    @classmethod
    def is_ssh_olt(cls, olt: str) -> bool:
        return olt not in cls.NON_SSH_OLTS

    @staticmethod
    def _slot_number(slot: str) -> str:
        return str(int(slot.rsplit(" ", 1)[-1]))

    @staticmethod
    def _pon_number(pon: str) -> str:
        return str(int(pon.rsplit(" ", 1)[-1]))

    def _run_ssh(self, command: str) -> list[str]:
        self.ssh_client.execute_command(command)
        stdout = self.ssh_client.get_stdout()
        return stdout.splitlines() or ["(Sem alarmes)"]

    def get_onus(self, slot: str, pon: str) -> list[constants.ONU]:
        if not self.ssh_client:
            return []

        command = f"show interface gpon 1/{self._slot_number(slot)}/{self._pon_number(pon)} onu"
        lines = self._run_ssh(command=command)
        lines = lines[2:]

        onus: list[constants.ONU] = []

        for line in lines:
            onu_id = int(line.split()[1])
            onus.append(constants.ONU(id=onu_id + 1, label=f"ONU {onu_id:03d}"))

        return onus

    def run_onu_alarms(self, pon: str = "PON 001", onu: int | str = 1) -> list[str]:
        if self.ssh_client is None:
            return ["(Sem conexão SSH)"]

        pon_num = self._pon_number(pon)
        onu_num = self._onu_number(onu)
        onu_num = int(onu_num) - 1
        command = f'show alarm | include "gpon-1/1/{pon_num}/{onu_num} "'
        return self._run_ssh(command=command)

    def run_pon_alarms(self, pon_number: str = "PON 001") -> list[str]:
        pon_number = self._pon_number(pon=pon_number)
        return self._run_ssh(command=f"show alarm | include 1/1/{pon_number}/")
