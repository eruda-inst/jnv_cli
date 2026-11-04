import re
from typing import ClassVar, TypedDict

from ..clients.telnet_client import TelnetClient
from ..config import settings


class ONUFiberhome(TypedDict):
    id: int
    label: str
    status: str
    serial_number: str


class FiberhomeOLT:
    TELNET_OLTS: ClassVar[frozenset[str]] = frozenset({"OLT de Acija", "OLT de Newnet"})

    OLT_TELNET_HOSTNAMES: ClassVar[dict[str, str]] = {
        "OLT de Acija": settings.olt_acija_hostname,
        "OLT de Newnet": settings.olt_newnet_hostname,
    }

    def __init__(self, telnet_client: TelnetClient) -> None:
        self.telnet_client = telnet_client

    @staticmethod
    def _numberfy(value: str | int) -> int:
        if isinstance(value, int):
            return value
        return int(value.rsplit(" ", 1)[-1])

    def _get_onu_status(self, slot_num: int, pon_num: int) -> dict[int, str]:
        commands = ["cd /", "cd onu", f"show onu_state slot {slot_num} pon {pon_num}"]

        onu_re = re.compile(
            pattern=r"SLOT\s+\d+\s+PON\s+\d+\s+ONU\s+\d+\s+status\s+:\s+\w+\s?\w+."
        )
        onu_status_re = re.compile(pattern=r"active|inactive|power down|link loss")
        raw_lines = self._run_commands(commands=commands)

        status_map = {}

        for raw_line in raw_lines:
            match = re.search(pattern=onu_re, string=raw_line)
            if match is not None:
                raw_result = match.group()
                result = raw_result.strip().removesuffix(".")
                parts = result.split()
                onu_id = int(parts[5])
                onu_status = "---"
                match = re.search(pattern=onu_status_re, string=result)

                if match is not None:
                    onu_status = match.group()

                status_map[onu_id] = onu_status

        return status_map

    def _run_commands(self, commands: list[str]) -> list[str]:
        client = self.telnet_client

        if len(commands) > 1:
            last_command = commands[-1]
            commands.pop(-1)
            for command in commands:
                client.send_command(command=command)
        else:
            last_command = commands[0]

        output = client.send_command(command=last_command)
        return output.splitlines()

    @classmethod
    def is_telnet_olt(cls, olt: str) -> bool:
        return olt in cls.TELNET_OLTS

    def get_onu_label(self, onu: ONUFiberhome, status_width: int = 0) -> str:
        onu_label = onu["label"]
        onu_status = onu["status"].ljust(status_width)
        onu_serial_number = onu["serial_number"]
        if onu_serial_number:
            return f"{onu_label} — {onu_status} — {onu_serial_number}"
        return f"{onu_label} — {onu_status}"

    def get_onus(
        self, slot: str = "SLOT 001", pon: str = "PON 001"
    ) -> list[ONUFiberhome]:
        slot_num = self._numberfy(value=slot)
        pon_num = self._numberfy(value=pon)

        commands = [
            "cd /",
            "cd onu",
            f"show authorization slot {slot_num} pon {pon_num}",
        ]

        raw_lines = self._run_commands(commands=commands)
        status_map = self._get_onu_status(slot_num=slot_num, pon_num=pon_num)

        onus = []

        for raw_line in raw_lines:
            pattern = re.compile(
                pattern=r"\d+\s+\d+\s+\d+\s+(\w+-?\w{0,}-?\w{0,})\s+\w+\s+\d+\s+\w{2}\s+\w{12}"
            )
            match = re.search(pattern=pattern, string=raw_line)

            if match is not None:
                raw_result = match.group()
                result = raw_result.strip()

                parts = result.split()

                onu_id = int(parts[2])
                onu_status = status_map.get(onu_id, "---")
                onu_serial = parts[7]

                self._get_onu_status(slot_num=slot_num, pon_num=pon_num)

                onus.append(
                    ONUFiberhome(
                        id=onu_id,
                        label=f"ONU {onu_id:03d}",
                        status=onu_status,
                        serial_number=onu_serial,
                    )
                )

        return onus

    def filter_onus(
        self, onus: list[ONUFiberhome], filter_code: str | None
    ) -> list[ONUFiberhome]:
        if filter_code is None:
            return onus
        if filter_code == "active":
            return [o for o in onus if o["status"].lower() == "active"]
        if filter_code == "inactive":
            return [o for o in onus if o["status"].lower() == "inactive"]
        if filter_code == "link loss":
            return [o for o in onus if o["status"].lower() == "link loss"]
        if filter_code == "power down":
            return [o for o in onus if o["status"].lower() == "power down"]
        return onus

    def run_pon_alarms(self, slot: str = "SLOT 001", pon: str = "PON 001") -> list[str]:
        slot_number = self._numberfy(value=slot)
        pon_number = self._numberfy(value=pon)

        commands = [
            "cd /",
            "cd onu",
            f"show onu_state slot {slot_number} pon {pon_number}",
        ]

        raw_lines = self._run_commands(commands=commands)
        alarms = []

        for raw_line in raw_lines:
            pattern = re.compile(
                pattern=r"SLOT\s+\d+\s+PON\s+\d+\s+ONU\s+\d+\s+status\s+:\s+\w+\s?\w+."
            )
            match = re.search(pattern=pattern, string=raw_line)

            if match is not None:
                raw_result = match.group()
                result = raw_result.strip().removesuffix(".")
                alarms.append(result)

        return alarms if len(alarms) else ["(Sem alarmes)"]

    def run_onu_alarms(
        self, slot: str = "SLOT 001", pon: str = "PON 001", onu: int | str = 1
    ) -> list[str]:
        slot_num = self._numberfy(value=slot)
        pon_num = self._numberfy(value=pon)
        onu_num = self._numberfy(value=onu)

        commands = [
            "cd /",
            "cd maintenance",
            "cd alarm",
            f"show alarm current obj 1/{slot_num}/{pon_num}/{onu_num}",
        ]

        raw_lines = self._run_commands(commands=commands)
        alarms = []

        for raw_line in raw_lines:
            pattern = re.compile(
                r"\d+\s+[A-Z_]+\s+\d+\s+\d+/\d+/\d+/\d+\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}"
            )
            match = re.search(pattern=pattern, string=raw_line)

            if match is not None:
                raw_result = match.group()
                result = raw_result.strip()
                alarms.append(result)

        return alarms if len(alarms) else ["(Sem alarmes)"]
