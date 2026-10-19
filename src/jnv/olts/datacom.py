from .. import clients, config, constants


class DatacomOLT:
    NON_SSH_OLTS: frozenset[str] = frozenset({"OLT ACIJA", "OLT NEWNET"})

    OLT_SSH_HOSTNAMES: dict[str, str] = {
        "OLT ITAITU": config.settings.olt_itaitu_hostname,
        "OLT JAC 3": config.settings.olt_jac_3_hostname,
        "OLT LAJES": config.settings.olt_lajes_hostname,
        "OLT PALMEIRINHA": config.settings.olt_palmeirinha_hostname,
        "OLT PARAÍSO": config.settings.olt_paraiso_hostname,
    }

    def __init__(self, ssh_client: clients.SSHClient | None = None) -> None:
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

    def _run_ssh(
        self, command: str, ssh_client: clients.SSHClient | None = None
    ) -> list[str]:
        client = ssh_client or self.ssh_client
        if not client:
            return ["(sem saída)"]
        client.execute_command(command)
        stdout = client.get_stdout()
        return stdout.splitlines() or ["(sem saída)"]

    def get_pons(self, ssh_client: clients.SSHClient | None = None) -> list[str]:
        client = ssh_client or self.ssh_client
        if not client or not client.is_connected:
            return [f"PON {i:03d}" for i in range(1, 8 + 1)]

        lines = self._run_ssh("show interface gpon brief", ssh_client=client)

        data_lines = [
            line.strip()
            for line in lines
            if line.strip()
            and not line.strip().startswith("Interface")
            and not line.strip().startswith("-")
        ]

        pons: list[str] = []
        for line in data_lines:
            parts = line.split()
            if parts:
                iface_parts = parts[0].split("/")
                if len(iface_parts) == 3:
                    try:
                        pon_num = int(iface_parts[2])
                        pons.append(f"PON {pon_num:03d}")
                    except ValueError:
                        pass

        if not pons and data_lines:
            pons = [f"PON {i:03d}" for i in range(1, len(data_lines) + 1)]

        return pons or [f"PON {i:03d}" for i in range(1, 8 + 1)]

    def get_onus(
        self, slot: str, pon: str, ssh_client: clients.SSHClient | None = None
    ) -> list[constants.ONU]:
        client = ssh_client or self.ssh_client
        if not client or not client.is_connected:
            return []

        command = f"show interface gpon 1/{self._slot_number(slot)}/{self._pon_number(pon)} onu"
        lines = self._run_ssh(command, ssh_client=client)
        lines = lines[2:]
        onus: list[constants.ONU] = []

        for i in range(len(lines)):
            onus.append(constants.ONU(id=i + 1, label=f"ONU {i:03d}"))

        return onus

    def run_onu_alarms(
        self,
        slot: str = "SLOT 001",
        pon: str = "PON 001",
        onu: int | str = 1,
        ssh_client: clients.SSHClient | None = None,
    ) -> list[str]:
        client = ssh_client or self.ssh_client
        if client is None or not client.is_connected:
            return ["(sem conexão SSH)"]

        pon_num = self._pon_number(pon)
        onu_num = self._onu_number(onu)
        onu_num = int(onu_num) - 1
        command = f'show alarm | include "gpon-1/1/{pon_num}/{onu_num} "'
        with open("file.txt", "wt") as file:
            file.write(command)
        return self._run_ssh(command, ssh_client=client)

    def run_pon_alarms(self, ssh_client: clients.SSHClient | None = None) -> list[str]:
        client = ssh_client or self.ssh_client
        if client is not None and client.is_connected:
            return self._run_ssh("show alarm", ssh_client=client)
        return ["(sem conexão SSH)"]
