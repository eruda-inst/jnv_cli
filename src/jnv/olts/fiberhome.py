import re
from typing import ClassVar

from .. import clients, config, constants


class FiberhomeOLT:
    TELNET_OLTS: ClassVar[frozenset[str]] = frozenset({"OLT ACIJA", "OLT NEWNET"})

    OLT_TELNET_HOSTNAMES: ClassVar[dict[str, str]] = {
        "OLT ACIJA": config.settings.olt_acija_hostname,
        "OLT NEWNET": config.settings.olt_newnet_hostname,
    }

    def __init__(self, telnet_client: clients.TelnetClient) -> None:
        self.telnet_client = telnet_client

    @classmethod
    def is_telnet_olt(cls, olt: str) -> bool:
        return olt in cls.TELNET_OLTS

    @staticmethod
    def _slot_number(slot: str) -> str:
        raw = slot.rsplit(" ", 1)[-1]
        if "/" in raw:
            raw = raw.split("/")[0]
        try:
            return str(int(raw))
        except ValueError:
            return raw

    @staticmethod
    def _pon_number(pon: str) -> str:
        raw = pon.rsplit(" ", 1)[-1]
        try:
            return str(int(raw))
        except ValueError:
            return raw

    @staticmethod
    def _onu_number(onu: int | str) -> str:
        if isinstance(onu, str):
            raw = onu.rsplit(" ", 1)[-1]
            try:
                return str(int(raw))
            except ValueError:
                return raw
        return str(onu)

    @staticmethod
    def _is_prompt_or_echo(line: str, commands: list[str]) -> bool:
        s = line.strip()
        if not s:
            return False

        for cmd in commands:
            cmd_clean = cmd.strip()
            if s == cmd_clean or s.startswith(cmd_clean):
                return True

        if re.match(r"^[A-Za-z0-9_\\/.\-]+[#>]$", s):
            return True

        return (
            "% Unknown command" in s
            or "Press any key to continue" in s
            or "Ctrl+c to stop" in s
            or "can not find the dir" in s
            or "Command executes failed" in s
            or 'You can input "dir"' in s
            or "to go to father dir" in s
            or "Connected to" in s
            or "force exit telnet" in s
            or "Press Ctrl-Q or Ctrl-Y" in s
        )

    def _run_telnet_commands(
        self, commands: list[str], cleanup_commands: list[str] | None = None
    ) -> list[str]:
        if not self.telnet_client or not self.telnet_client.is_connected:
            return ["(Sem conexão Telnet)"]

        cleanup = cleanup_commands or ["cd /"]
        all_cmds = commands + cleanup
        output_lines: list[str] = []

        try:
            for cmd in commands:
                res = self.telnet_client.send_command(cmd)
                if res.strip():
                    for line in res.splitlines():
                        if not self._is_prompt_or_echo(line, all_cmds):
                            output_lines.append(line)
        finally:
            for clean_cmd in cleanup:
                self.telnet_client.send_command(clean_cmd)

        while output_lines and not output_lines[0].strip():
            output_lines.pop(0)
        while output_lines and not output_lines[-1].strip():
            output_lines.pop()

        return output_lines or ["(Sem saída ou sem alarmes registrados)"]

    def get_onus(
        self, slot: str = "SLOT 001", pon: str = "PON 001"
    ) -> list[constants.ONU]:
        if not self.telnet_client or not self.telnet_client.is_connected:
            return []

        slot_num = self._slot_number(slot)
        pon_num = self._pon_number(pon)
        cmds = ["cd /", "cd onu", f"show onu_state slot {slot_num} pon {pon_num}"]
        lines = self._run_telnet_commands(commands=cmds)

        onus: list[constants.ONU] = []
        for line in lines:
            parts = line.strip().split()
            if parts and parts[0].isdigit():
                try:
                    onu_id = int(parts[0])
                    onus.append(constants.ONU(id=onu_id, label=f"ONU {onu_id:03d}"))
                except ValueError:
                    pass

        if not onus:
            data_lines = [
                l
                for l in lines
                if l.strip()
                and not l.strip().startswith("cd")
                and not l.strip().startswith("show")
            ]
            for i in range(len(data_lines)):
                onus.append(constants.ONU(id=i + 1, label=f"ONU {i + 1:03d}"))

        return onus

    get_onu = get_onus

    def run_pon_alarms(self, slot: str = "SLOT 001", pon: str = "PON 001") -> list[str]:
        if not self.telnet_client or not self.telnet_client.is_connected:
            return ["(Sem conexão Telnet)"]

        slot_number = self._slot_number(slot)
        pon_number = self._pon_number(pon)
        commands = [
            "cd /",
            "cd onu",
            f"show onu_state slot {slot_number} pon {pon_number}",
        ]
        return self._run_telnet_commands(commands=commands)

    def run_onu_alarms(
        self, slot: str = "SLOT 001", pon: str = "PON 001", onu: int | str = 1
    ) -> list[str]:
        if not self.telnet_client or not self.telnet_client.is_connected:
            return ["(Sem conexão Telnet)"]

        slot_num = self._slot_number(slot)
        pon_num = self._pon_number(pon)
        onu_num = self._onu_number(onu)

        commands = [
            "cd /",
            "cd maintenance",
            "cd alarm",
            f"show alarm current obj 1/{slot_num}/{pon_num}/{onu_num}",
        ]

        cleanup = ["cd /"]

        return self._run_telnet_commands(commands=commands, cleanup_commands=cleanup)
