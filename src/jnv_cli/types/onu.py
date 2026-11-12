from dataclasses import dataclass


@dataclass
class ONUDatacom:
    id: int
    serial: str
    ost: str
    name: str

    @property
    def label(self) -> str:
        return f"ONU {self.id:03d}"


@dataclass
class ONUFiberhome:
    id: int
    ost: str
    serial: str
    status: str

    @property
    def label(self) -> str:
        return f"ONU {self.id:03d}"
