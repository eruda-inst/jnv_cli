import re
from dataclasses import dataclass, replace

from jnv_cli.utils import NO_ALARM_LABEL, NONE_LABEL


@dataclass
class DatacomPONAlarm:
    type: str
    source_value: str
    name: str
    info: str
    time: str
    unstable: str
    severity: str


def build_datacom_pon_alarms(raw_lines: list[str]) -> list[str]:
    alarms = []

    if raw_lines == [NO_ALARM_LABEL]:
        return raw_lines

    for raw_line in raw_lines:
        alarm = raw_line.strip()
        parts = alarm.split()

        type = NONE_LABEL
        source_value = NONE_LABEL
        name = NONE_LABEL
        info = NONE_LABEL
        time = NONE_LABEL
        unstable = NONE_LABEL
        severity = NONE_LABEL

        if len(parts) >= 1:
            type = parts[0]

        if len(parts) >= 2:
            source_value = parts[1]
            severity = parts[-1]

        if len(parts) >= 3:
            name = parts[2]
            unstable = parts[-2]

        INFO_RE = re.compile(
            pattern=r"ONU Loss of signal|Receive dying gasp of ONU|Deactivate failure of ONU|Loss of PLOAM for ONU|Drift of the window of ONU|Transmission interference warning of ONU|Loss of frame of ONU"
        )
        match_info = INFO_RE.search(string=alarm)
        if match_info is not None:
            info = match_info.group()

        TIME_RE = re.compile(pattern=r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC[\+-]\d")
        match_time = TIME_RE.search(string=alarm)
        if match_time is not None:
            time = match_time.group()

        alarms.append(
            DatacomPONAlarm(
                type=type,
                source_value=source_value,
                name=name,
                info=info,
                time=time,
                unstable=unstable,
                severity=severity,
            )
        )

    max_type = max([len(alarm.type) for alarm in alarms], default=0)
    max_source_value = max([len(alarm.source_value) for alarm in alarms], default=0)
    max_name = max([len(alarm.name) for alarm in alarms], default=0)
    max_info = max([len(alarm.info) for alarm in alarms], default=0)
    max_time = max([len(alarm.time) for alarm in alarms], default=0)
    max_unstable = max([len(alarm.unstable) for alarm in alarms], default=0)
    max_severity = max([len(alarm.severity) for alarm in alarms], default=0)

    h1 = "TYPE"
    h2 = "SOURCE VALUE"
    h3 = "NAME"
    h4 = "INFO"
    h5 = "TIME"
    h6 = "UNSTABLE"
    h7 = "SEVERITY"

    if max_type > len(h1):
        h1 = h1.ljust(max_type)
    else:
        max_type = len(h1)

    if max_source_value > len(h2):
        h2 = h2.ljust(max_source_value)
    else:
        max_source_value = len(h2)

    if max_name > len(h3):
        h3 = h3.ljust(max_name)
    else:
        max_name = len(h3)

    if max_info > len(h4):
        h4 = h4.ljust(max_info)
    else:
        max_info = len(h4)

    if max_time > len(h5):
        h5 = h5.ljust(max_time)
    else:
        max_time = len(h5)

    if max_unstable > len(h6):
        h6 = h6.ljust(max_unstable)
    else:
        max_unstable = len(h6)

    if max_severity > len(h7):
        h7 = h7.ljust(max_severity)
    else:
        max_severity = len(h7)

    alarms = [replace(alarm, type=alarm.type.ljust(max_type)) for alarm in alarms]
    alarms = [
        replace(alarm, source_value=alarm.source_value.ljust(max_source_value))
        for alarm in alarms
    ]
    alarms = [replace(alarm, name=alarm.name.ljust(max_name)) for alarm in alarms]
    alarms = [replace(alarm, info=alarm.info.ljust(max_info)) for alarm in alarms]
    alarms = [replace(alarm, time=alarm.time.ljust(max_time)) for alarm in alarms]
    alarms = [
        replace(alarm, unstable=alarm.unstable.ljust(max_unstable)) for alarm in alarms
    ]
    alarms = [
        replace(alarm, severity=alarm.severity.ljust(max_severity)) for alarm in alarms
    ]

    hs = f"{h1}   {h2}   {h3}   {h4}   {h5}   {h6}   {h7}"
    dashes = "-" * len(hs)

    output = []
    output.append(hs)
    output.append(dashes)

    for alarm in alarms:
        output.append(
            f"{alarm.type}   {alarm.source_value}   {alarm.name}   {alarm.info}   {alarm.time}   {alarm.unstable}   {alarm.severity}"
        )

    return output
