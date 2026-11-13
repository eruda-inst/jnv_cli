import re
from dataclasses import replace
from typing import ClassVar

from jnv_cli.clients.telnet_client import TelnetClient
from jnv_cli.config import settings
from jnv_cli.types.olt_names import OLTNames
from jnv_cli.types.onu import ONUFiberhome
from jnv_cli.utils import NO_ALARM_LABEL, NONE_LABEL, SERIAL_FILTER_SENTINEL, numberfy

FIBERHOME_ALARM_FILTER_CODES = (
    None,
    SERIAL_FILTER_SENTINEL,
    "active",
    "inactive",
    "link loss",
    "power down",
)
FIBERHOME_ALARM_FILTER_LABELS = (
    "Todas",
    "Digite o serial number da ONU",
    "ONUs sem alarmes",
    "ONUs inativas (LOS ou Dying Gasp)",
    "ONUs com perda de sinal (LOS)",
    "ONUs com perda de energia (Dying Gasp)",
)
FIBERHOME_ALARM_FILTERS = [
    (FIBERHOME_ALARM_FILTER_CODES[i], FIBERHOME_ALARM_FILTER_LABELS[i])
    for i in range(len(FIBERHOME_ALARM_FILTER_LABELS))
]


class FiberhomeOLT:
    _PON_ALARM_RE: ClassVar[re.Pattern[str]] = re.compile(
        pattern=r"SLOT\s+\d+\s+PON\s+\d+\s+ONU\s+\d+\s+status\s+:\s+\w+\s?\w+."
    )
    _ONU_ALARM_RE: ClassVar[re.Pattern[str]] = re.compile(
        pattern=r"\d+\s+[A-Z_]+\s+\d+\s+\d+/\d+/\d+/\d+\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}"
    )
    _ONU_RE: ClassVar[re.Pattern[str]] = re.compile(
        pattern=r"\d+\s+\d+\s+\d+\s+(\w+-?\w{0,}-?\w{0,})\s+\w+\s+\d+\s+\w{2}\s+\w{12}"
    )
    _ONU_STATUS_RE: ClassVar[re.Pattern[str]] = re.compile(
        pattern=r"active|inactive|power down|link loss"
    )
    FIBERHOME_HOSTNAMES: ClassVar[dict[OLTNames, str]] = {
        OLTNames.ACIJA: settings.olt_acija_hostname,
        OLTNames.NEWNET: settings.olt_newnet_hostname,
    }

    def __init__(self, telnet_client: TelnetClient) -> None:
        self.client = telnet_client

    def _run_commands(self, commands: list[str]) -> list[str]:
        last_command = commands[0]

        if len(commands) > 1:
            last_command = commands[-1]
            commands.pop(-1)
            for command in commands:
                self.client.send_command(command=command)

        output = self.client.send_command(command=last_command)
        return output.splitlines()

    def _get_onu_status(self, slot_num: int, pon_num: int) -> dict[int, str]:
        commands = ["cd /onu", f"show onu_state slot {slot_num} pon {pon_num}"]
        raw_lines = self._run_commands(commands=commands)
        status_map = {}

        for raw_line in raw_lines:
            match = self._PON_ALARM_RE.search(string=raw_line)

            if match is not None:
                raw_result = match.group()
                result = raw_result.strip().removesuffix(".")
                parts = result.split()
                onu_id = int(parts[5])

                onu_status = NONE_LABEL
                match = self._ONU_STATUS_RE.search(string=result)
                if match is not None:
                    onu_status = match.group()

                status_map[onu_id] = onu_status

        return status_map

    @classmethod
    def is_fiberhome_olt(cls, olt: str) -> bool:
        return olt in cls.FIBERHOME_HOSTNAMES

    def get_onus(
        self, slot: str = "SLOT 001", pon: str = "PON 001"
    ) -> list[ONUFiberhome]:
        slot_num = numberfy(value=slot)
        pon_num = numberfy(value=pon)

        commands = [
            "cd /onu",
            f"show authorization slot {slot_num} pon {pon_num}",
        ]

        raw_lines = self._run_commands(commands=commands)
        status_map = self._get_onu_status(slot_num=slot_num, pon_num=pon_num)
        onus = []

        for raw_line in raw_lines:
            match = self._ONU_RE.search(string=raw_line)

            if match is not None:
                raw_result = match.group()
                result = raw_result.strip()
                parts = result.split()

                id = int(parts[2])
                ost = "Up" if parts[6] == "up" else "Down"
                serial = parts[7]
                status = status_map.get(id, NONE_LABEL)

                onus.append(ONUFiberhome(id=id, ost=ost, serial=serial, status=status))

        max_ost = max([len(onu.ost) for onu in onus], default=0)
        onus = [replace(onu, ost=onu.ost.ljust(max_ost)) for onu in onus]

        return onus

    @staticmethod
    def filter_onus(
        onus: list[ONUFiberhome], filter_code: str | None
    ) -> list[ONUFiberhome]:
        if filter_code is None:
            return onus
        return [onu for onu in onus if onu.status == filter_code]

    def get_pon_alarms(self, slot: str = "SLOT 001", pon: str = "PON 001") -> list[str]:
        slot_number = numberfy(value=slot)
        pon_number = numberfy(value=pon)

        commands = [
            "cd /onu",
            f"show onu_state slot {slot_number} pon {pon_number}",
        ]

        raw_lines = self._run_commands(commands=commands)
        alarms = []

        for raw_line in raw_lines:
            match = self._PON_ALARM_RE.search(string=raw_line)

            if match is not None:
                raw_result = match.group()
                result = raw_result.strip().removesuffix(".")
                alarms.append(result)

        return alarms if len(alarms) else [NO_ALARM_LABEL]

    def get_onu_alarms(
        self, slot: str = "SLOT 001", pon: str = "PON 001", onu: int | str = 1
    ) -> list[str]:
        slot_num = numberfy(value=slot)
        pon_num = numberfy(value=pon)
        onu_num = numberfy(value=onu)

        commands = [
            "cd /maintenance/alarm",
            f"show alarm current obj 1/{slot_num}/{pon_num}/{onu_num}",
        ]

        raw_lines = self._run_commands(commands=commands)
        alarm_raw_lines = []

        for raw_line in raw_lines:
            match = self._ONU_ALARM_RE.search(string=raw_line)

            if match is not None:
                alarm_raw_lines.append(raw_line)

        return alarm_raw_lines if len(alarm_raw_lines) else [NO_ALARM_LABEL]
