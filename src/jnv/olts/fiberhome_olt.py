import re
from typing import ClassVar, TypedDict

from ..clients.telnet_client import TelnetClient
from ..config import settings


class ONUFiberhome(TypedDict):
    id: int
    label: str
    status: str


class FiberhomeOLT:
    TELNET_OLTS: ClassVar[frozenset[str]] = frozenset({"OLT ACIJA", "OLT NEWNET"})

    OLT_TELNET_HOSTNAMES: ClassVar[dict[str, str]] = {
        "OLT ACIJA": settings.olt_acija_hostname,
        "OLT NEWNET": settings.olt_newnet_hostname,
    }

    def __init__(self, telnet_client: TelnetClient) -> None:
        self.telnet_client = telnet_client

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

    def _run_telnet_commands(self, commands: list[str]) -> list[str]:
        output_lines: list[str] = []

        for command in commands:
            res = self.telnet_client.send_command(command)
            for line in res.splitlines():
                if line.strip() and not self._is_prompt_or_echo(line, commands):
                    output_lines.append(line.strip().removesuffix("."))

        return output_lines or ["(Sem saída ou sem alarmes registrados)"]

    @classmethod
    def is_telnet_olt(cls, olt: str) -> bool:
        return olt in cls.TELNET_OLTS

    def get_onu_label(self, onu: ONUFiberhome) -> str:
        onu_label = onu["label"]
        onu_status = onu["status"]
        return f"{onu_label} — {onu_status}"

    def get_onus(
        self, slot: str = "SLOT 001", pon: str = "PON 001"
    ) -> list[ONUFiberhome]:
        slot_num = self._slot_number(slot)
        pon_num = self._pon_number(pon)
        cmds = ["cd /", "cd onu", f"show onu_state slot {slot_num} pon {pon_num}"]
        lines = self._run_telnet_commands(commands=cmds)

        onus: list[ONUFiberhome] = []
        for line in lines:
            if "status" not in line or ":" not in line:
                continue

            parts = line.split()
            if len(parts) < 9:
                continue

            try:
                onu_id = int(parts[5])
                onu_status = line.split(":", 1)[1].strip().removesuffix(".")

                onus.append(
                    ONUFiberhome(
                        id=onu_id,
                        label=f"ONU {onu_id:03d}",
                        status=onu_status,
                    )
                )
            except ValueError, IndexError:
                continue

        return onus

    def filter_onus(
        self, onus: list[ONUFiberhome], filter_code: str | None
    ) -> list[ONUFiberhome]:
        if filter_code is None:
            return onus
        if filter_code == "Active":
            return [o for o in onus if o["status"].lower() == "active"]
        if filter_code == "Inactive":
            return [o for o in onus if o["status"].lower() == "inactive"]
        if filter_code == "Link loss":
            return [o for o in onus if o["status"].lower() == "link loss"]
        if filter_code == "Power down":
            return [o for o in onus if o["status"].lower() == "power down"]
        return onus

    def run_pon_alarms(self, slot: str = "SLOT 001", pon: str = "PON 001") -> list[str]:
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
        slot_num = self._slot_number(slot)
        pon_num = self._pon_number(pon)
        onu_num = self._onu_number(onu)

        commands = [
            "cd /",
            "cd maintenance",
            "cd alarm",
            f"show alarm current obj 1/{slot_num}/{pon_num}/{onu_num}",
        ]

        return self._run_telnet_commands(commands=commands)
