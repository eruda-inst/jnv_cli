import re
from typing import ClassVar, TypedDict

from ..clients.telnet_client import TelnetClient
from ..config import settings


class ONUFiberhome(TypedDict):
    id: int
    label: str
    status: str


class FiberhomeOLT:
    TELNET_OLTS: ClassVar[frozenset[str]] = frozenset({"OLT de Acija", "OLT de Newnet"})

    OLT_TELNET_HOSTNAMES: ClassVar[dict[str, str]] = {
        "OLT de Acija": settings.olt_acija_hostname,
        "OLT de Newnet": settings.olt_newnet_hostname,
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

        output = self.telnet_client.send_command(command="cd /")
        output = self.telnet_client.send_command(command="cd onu")
        output = self.telnet_client.send_command(
            command=f"show onu_state slot {slot_num} pon {pon_num}"
        )

        raw_lines = output.splitlines()
        onus = []

        for raw_line in raw_lines:
            pattern = re.compile(
                pattern=r"SLOT\s+\d+\s+PON\s+\d+\s+ONU\s+\d+\s+status\s+:\s+\w+\s?\w+."
            )
            match = re.match(pattern=pattern, string=raw_line)

            if match is not None:
                raw_result = match.group()
                result = raw_result.strip().removesuffix(".")

                parts = result.split()
                onu_id = int(parts[5])

                onu_status = "---"
                pattern = re.compile(pattern=r"power down|inactive|active|link loss")
                match = re.search(pattern=pattern, string=result)
                if match is not None:
                    onu_status = match.group()

                onus.append(
                    ONUFiberhome(
                        id=onu_id,
                        label=f"ONU {onu_id:03d}",
                        status=onu_status,
                    )
                )

        return onus if len(onus) else ["(Sem alarmes)"]

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

        output = self.telnet_client.send_command("cd /")
        output = self.telnet_client.send_command("cd onu")
        output = self.telnet_client.send_command(
            f"show onu_state slot {slot_number} pon {pon_number}"
        )

        raw_lines = output.splitlines()
        alarms = []

        for raw_line in raw_lines:
            pattern = re.compile(
                r"SLOT\s+\d+\s+PON\s+\d+\s+ONU\s+\d+\s+status\s+:\s+\w+\s?\w+."
            )
            match = re.match(pattern=pattern, string=raw_line)

            if match is not None:
                raw_result = match.group()
                result = raw_result.strip().removesuffix(".")
                alarms.append(result)

        return alarms if len(alarms) else ["(Sem alarmes)"]

    def run_onu_alarms(
        self, slot: str = "SLOT 001", pon: str = "PON 001", onu: int | str = 1
    ) -> list[str]:
        slot_num = self._slot_number(slot)
        pon_num = self._pon_number(pon)
        onu_num = self._onu_number(onu)

        output = self.telnet_client.send_command("cd /")
        output = self.telnet_client.send_command("cd maintenance")
        output = self.telnet_client.send_command("cd alarm")
        output = self.telnet_client.send_command(
            f"show alarm current obj 1/{slot_num}/{pon_num}/{onu_num}"
        )

        raw_lines = output.splitlines()
        alarms = []

        for raw_line in raw_lines:
            pattern = re.compile(
                r"\d+\s+[A-Z_]+\s+\d+\s+\d+/\d+/\d+/\d+\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}"
            )
            match = re.match(pattern=pattern, string=raw_line)

            if match is not None:
                raw_result = match.group()
                result = raw_result.strip()
                alarms.append(result)

        return alarms if len(alarms) else ["(Sem alarmes)"]
