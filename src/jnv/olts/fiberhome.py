import re
from typing import ClassVar

from .. import clients, config, constants


class FiberhomeOLT:
    TELNET_OLTS: ClassVar[frozenset[str]] = frozenset({"OLT ACIJA", "OLT NEWNET"})

    OLT_TELNET_HOSTNAMES: ClassVar[dict[str, str]] = {
        "OLT ACIJA": config.settings.olt_acija_hostname,
        "OLT NEWNET": config.settings.olt_newnet_hostname,
    }

    def __init__(self, telnet_client: clients.TelnetClient | None = None) -> None:
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

        if any(
            err in s
            for err in (
                "% Unknown command",
                "Press any key to continue",
                "Ctrl+c to stop",
                "can not find the dir",
                "Command executes failed",
                'You can input "dir"',
                "to go to father dir",
                "Connected to",
                "force exit telnet",
                "Press Ctrl-Q or Ctrl-Y",
            )
        ):
            return True

        return False

    def _run_telnet_commands(
        self,
        commands: list[str],
        telnet_client: clients.TelnetClient | None = None,
        cleanup_commands: list[str] | None = None,
    ) -> list[str]:
        client = telnet_client or self.telnet_client
        if not client or not client.is_connected:
            return ["(Sem conexão Telnet)"]

        cleanup = cleanup_commands or ["cd /"]
        all_cmds = commands + cleanup
        output_lines: list[str] = []

        try:
            for cmd in commands:
                res = client.send_command(cmd)
                if res.strip():
                    for line in res.splitlines():
                        if not self._is_prompt_or_echo(line, all_cmds):
                            output_lines.append(line)
        finally:
            for clean_cmd in cleanup:
                try:
                    client.send_command(clean_cmd)
                except Exception:
                    pass

        while output_lines and not output_lines[0].strip():
            output_lines.pop(0)
        while output_lines and not output_lines[-1].strip():
            output_lines.pop()

        return output_lines or ["(Sem saída ou sem alarmes registrados)"]

    def get_pons(
        self,
        slot: str = "SLOT 001",
        telnet_client: clients.TelnetClient | None = None,
    ) -> list[str]:
        client = telnet_client or self.telnet_client
        if not client or not client.is_connected:
            return [f"PON {i:03d}" for i in range(1, 16 + 1)]

        slot_num = self._slot_number(slot)
        cmds = ["cd /", "cd card", f"show pon_onoff {slot_num}"]
        lines = self._run_telnet_commands(cmds, telnet_client=client)

        pons: list[str] = []
        for line in lines:
            match = re.search(r"PON\s*(\d+)", line, re.IGNORECASE)
            if match:
                pon_num = int(match.group(1))
                pon_str = f"PON {pon_num:03d}"
                if pon_str not in pons:
                    pons.append(pon_str)

        if not pons:
            pons = [f"PON {i:03d}" for i in range(1, 16 + 1)]

        return pons

    def get_onus(
        self,
        slot: str = "SLOT 001",
        pon: str = "PON 001",
        telnet_client: clients.TelnetClient | None = None,
    ) -> list[constants.ONU]:
        client = telnet_client or self.telnet_client
        if not client or not client.is_connected:
            return []

        slot_num = self._slot_number(slot)
        pon_num = self._pon_number(pon)
        cmds = ["cd /", "cd onu", f"show onu_state slot {slot_num} pon {pon_num}"]
        lines = self._run_telnet_commands(cmds, telnet_client=client)

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

    def run_pon_alarms(
        self,
        slot: str = "SLOT 001",
        pon: str = "PON 001",
        telnet_client: clients.TelnetClient | None = None,
    ) -> list[str]:
        client = telnet_client or self.telnet_client
        if not client or not client.is_connected:
            return ["(Sem conexão Telnet)"]

        slot_num = self._slot_number(slot)
        pon_num = self._pon_number(pon)
        cmds = ["cd /", "cd onu", f"show onu_state slot {slot_num} pon {pon_num}"]
        return self._run_telnet_commands(cmds, telnet_client=client)

    def run_onu_alarms(
        self,
        slot: str = "SLOT 001",
        pon: str = "PON 001",
        onu: int | str = 1,
        telnet_client: clients.TelnetClient | None = None,
    ) -> list[str]:
        client = telnet_client or self.telnet_client
        if not client or not client.is_connected:
            return ["(Sem conexão Telnet)"]

        slot_num = self._slot_number(slot)
        pon_num = self._pon_number(pon)
        onu_num = self._onu_number(onu)

        cmds = [
            "cd /",
            "cd maintenance",
            "cd alarm",
            f"show alarm current obj 1/{slot_num}/{pon_num}/{onu_num}",
        ]

        cleanup = ["cd /"]

        return self._run_telnet_commands(
            cmds, telnet_client=client, cleanup_commands=cleanup
        )
