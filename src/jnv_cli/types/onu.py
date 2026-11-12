from dataclasses import dataclass


@dataclass
class ONUDatacom:
    id: int
    label: str
    serial: str
    ost: str
    name: str


@dataclass
class ONUFiberhome:
    id: int
    label: str
    ost: str
    serial: str
    status: str
