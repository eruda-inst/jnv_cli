import re
from typing import ClassVar, TypedDict

from jnv_cli.clients.telnet_client import TelnetClient
from jnv_cli.config import settings
from jnv_cli.constants import NONE_SUBSTITUTE
from jnv_cli.utils import join_values, numberfy


class ONUFiberhome(TypedDict):
    id: int
    label: str
    status: str
    serial_number: str


class FiberhomeOLT:
    PON_ALARM_RE: ClassVar[re.Pattern[str]] = re.compile(
        pattern=r"SLOT\s+\d+\s+PON\s+\d+\s+ONU\s+\d+\s+status\s+:\s+\w+\s?\w+."
    )
    ONU_ALARM_RE: ClassVar[re.Pattern[str]] = re.compile(
        pattern=r"\d+\s+[A-Z_]+\s+\d+\s+\d+/\d+/\d+/\d+\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}"
    )
    ONU_RE: ClassVar[re.Pattern[str]] = re.compile(
        pattern=r"\d+\s+\d+\s+\d+\s+(\w+-?\w{0,}-?\w{0,})\s+\w+\s+\d+\s+\w{2}\s+\w{12}"
    )
    ONU_STATUS_RE: ClassVar[re.Pattern[str]] = re.compile(
        pattern=r"active|inactive|power down|link loss"
    )
    TELNET_OLTS: ClassVar[frozenset[str]] = frozenset({"OLT de Acija", "OLT de Newnet"})
    OLT_TELNET_HOSTNAMES: ClassVar[dict[str, str]] = {
        "OLT de Acija": settings.olt_acija_hostname,
        "OLT de Newnet": settings.olt_newnet_hostname,
    }

    def __init__(self, telnet_client: TelnetClient) -> None:
        self.telnet_client = telnet_client

    def _get_onu_status(self, slot_num: int, pon_num: int) -> dict[int, str]:
        commands = ["cd /", "cd onu", f"show onu_state slot {slot_num} pon {pon_num}"]

        raw_lines = self._run_commands(commands=commands)

        status_map = {}

        for raw_line in raw_lines:
            match = self.PON_ALARM_RE.search(string=raw_line)

            if match is not None:
                raw_result = match.group()
                result = raw_result.strip().removesuffix(".")
                parts = result.split()
                onu_id = int(parts[5])

                onu_status = NONE_SUBSTITUTE
                match = self.ONU_STATUS_RE.search(string=result)
                if match is not None:
                    onu_status = match.group()

                status_map[onu_id] = onu_status

        return status_map

    def _run_commands(self, commands: list[str]) -> list[str]:
        last_command = commands[0]

        if len(commands) > 1:
            last_command = commands[-1]
            commands.pop(-1)
            for command in commands:
                self.telnet_client.send_command(command=command)

        output = self.telnet_client.send_command(command=last_command)
        return output.splitlines()

    @classmethod
    def is_telnet_olt(cls, olt: str) -> bool:
        return olt in cls.TELNET_OLTS

    def get_onu_label(self, onu: ONUFiberhome, status_width: int = 0) -> str:
        onu_label = onu["label"]
        onu_status = onu["status"].ljust(status_width)
        onu_serial_number = onu["serial_number"]
        if onu_serial_number:
            return join_values(values=[onu_label, onu_status, onu_serial_number])
        return join_values(values=[onu_label, onu_status])

    def get_onus(
        self, slot: str = "SLOT 001", pon: str = "PON 001"
    ) -> list[ONUFiberhome]:
        slot_num = numberfy(value=slot)
        pon_num = numberfy(value=pon)

        commands = [
            "cd /",
            "cd onu",
            f"show authorization slot {slot_num} pon {pon_num}",
        ]

        raw_lines = self._run_commands(commands=commands)

        status_map = self._get_onu_status(slot_num=slot_num, pon_num=pon_num)

        onus = []

        for raw_line in raw_lines:
            match = self.ONU_RE.search(string=raw_line)

            if match is not None:
                raw_result = match.group()
                result = raw_result.strip()

                parts = result.split()

                onu_id = int(parts[2])
                onu_status = status_map.get(onu_id, NONE_SUBSTITUTE)
                onu_serial = parts[7]

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
        return [onu for onu in onus if onu["status"] == filter_code]

    def run_pon_alarms(self, slot: str = "SLOT 001", pon: str = "PON 001") -> list[str]:
        slot_number = numberfy(value=slot)
        pon_number = numberfy(value=pon)

        commands = [
            "cd /",
            "cd onu",
            f"show onu_state slot {slot_number} pon {pon_number}",
        ]

        raw_lines = self._run_commands(commands=commands)
        alarms = []

        for raw_line in raw_lines:
            match = self.PON_ALARM_RE.search(string=raw_line)

            if match is not None:
                raw_result = match.group()
                result = raw_result.strip().removesuffix(".")
                alarms.append(result)

        return alarms if len(alarms) else ["(Sem alarmes)"]

    def run_onu_alarms(
        self, slot: str = "SLOT 001", pon: str = "PON 001", onu: int | str = 1
    ) -> list[str]:
        slot_num = numberfy(value=slot)
        pon_num = numberfy(value=pon)
        onu_num = numberfy(value=onu)

        commands = [
            "cd /",
            "cd maintenance",
            "cd alarm",
            f"show alarm current obj 1/{slot_num}/{pon_num}/{onu_num}",
        ]

        raw_lines = self._run_commands(commands=commands)
        alarms = []

        for raw_line in raw_lines:
            match = self.ONU_ALARM_RE.search(string=raw_line)

            if match is not None:
                raw_result = match.group()
                result = raw_result.strip()
                alarms.append(result)

        return alarms if len(alarms) else ["(Sem alarmes)"]
