from dataclasses import dataclass


@dataclass
class FiberhomeONUAlarm:
    item: str
    description: str
    code: str
    object: str
    begintime: str
    endtime: str


@dataclass
class DatacomAlarm:
    type: str
    source_value: str
    name: str
    info: str
    time: str
    unstable: str
    severity: str
