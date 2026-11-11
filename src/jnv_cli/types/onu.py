from dataclasses import dataclass


@dataclass
class ONUDatacom:
    id: int
    label: str
    status: str
    serial: str
    name: str


@dataclass
class ONUFiberhome:
    id: int
    label: str
    status: str
    serial: str
