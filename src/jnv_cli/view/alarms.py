import re
from collections.abc import Sequence
from dataclasses import asdict, replace

from jnv_cli.types.alarms import (
    Alarms,
    DatacomAlarm,
    FiberhomeONUAlarm,
    FiberhomePONAlarm,
)
from jnv_cli.utils import NO_ALARM_LABEL, NONE_LABEL

COLUMN_SEPARATOR = " " * 3
HORIZONTAL_LINE_CHARACTER = "-"


def build_alarm_table_header_lines(cols: Sequence[str]) -> list[str]:
    cols = COLUMN_SEPARATOR.join(cols)
    horizontal_line = HORIZONTAL_LINE_CHARACTER * len(cols)

    return [cols, horizontal_line]


def build_alarm_table_rows(alarms: Alarms) -> list[str]:
    rows = []

    for alarm in alarms:
        alarm_dict = asdict(alarm)
        values = alarm_dict.values()
        rows.append(COLUMN_SEPARATOR.join(values))

    return rows


def build_fiberhome_pon_alarm_table(raw_alarms: list[str]) -> list[str]:
    if not raw_alarms:
        return [NO_ALARM_LABEL]

    alarms: list[FiberhomePONAlarm] = []

    for raw_alarm in raw_alarms:
        alarm = raw_alarm.strip().removesuffix(".")
        parts = alarm.split()

        slot = NONE_LABEL
        pon = NONE_LABEL
        onu = NONE_LABEL
        status = NONE_LABEL

        if len(parts) >= 2:
            slot = parts[1]

        if len(parts) >= 4:
            pon = parts[3]

        if len(parts) >= 6:
            onu = parts[5]

        STATUS_RE = re.compile(pattern=r"active|inactive|power down|link loss")
        status_match = STATUS_RE.search(string=alarm)
        if status_match is not None:
            status = status_match.group()

        alarms.append(
            FiberhomePONAlarm(
                slot=f"{int(slot):03d}",
                pon=f"{int(pon):03d}",
                onu=f"{int(onu):03d}",
                status=status,
            )
        )

    cols = ["SLOT", "PON", "ONU", "STATUS"]
    sizes = [
        max([len(alarm.slot) for alarm in alarms], default=0),
        max([len(alarm.pon) for alarm in alarms], default=0),
        max([len(alarm.onu) for alarm in alarms], default=0),
        max([len(alarm.status) for alarm in alarms], default=0),
    ]

    for i in range(len(cols)):
        max_size = max(len(cols[i]), sizes[i])
        cols[i] = cols[i].ljust(max_size)
        sizes[i] = max_size

    for alarm in alarms:
        alarm = replace(alarm, slot=alarm.slot.ljust(sizes[0]))
        alarm = replace(alarm, pon=alarm.pon.ljust(sizes[1]))
        alarm = replace(alarm, onu=alarm.onu.ljust(sizes[2]))
        alarm = replace(alarm, status=alarm.status.ljust(sizes[3]))

    table = []

    columns = build_alarm_table_header_lines(cols=cols)
    rows = build_alarm_table_rows(alarms=alarms)

    table.extend(columns)
    table.extend(rows)

    return table


def build_fiberhome_onu_alarm_table(raw_alarms: list[str]) -> list[str]:
    if not raw_alarms:
        return [NO_ALARM_LABEL]

    alarms: list[FiberhomeONUAlarm] = []

    for raw_alarm in raw_alarms:
        alarm = raw_alarm.strip()
        parts = alarm.split()

        item = NONE_LABEL
        description = NONE_LABEL
        code = NONE_LABEL
        object = NONE_LABEL
        begintime = NONE_LABEL
        endtime = NONE_LABEL

        if len(parts) >= 1:
            item = parts[0]

        if len(parts) >= 2:
            description = parts[1]

        if len(parts) >= 3:
            code = parts[2]

        if len(parts) >= 4:
            object = parts[3]

        TIME_RE = re.compile(pattern=r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
        time_match = TIME_RE.findall(string=alarm)
        if len(time_match) >= 1:
            begintime = time_match[0]
        if len(time_match) >= 2:
            endtime = time_match[1]

        alarms.append(
            FiberhomeONUAlarm(
                item=f"{int(item):03d}",
                description=description,
                code=f"{int(code):03d}",
                object=object,
                begintime=begintime,
                endtime=endtime,
            )
        )

    cols = ["ITEM", "DESCRIPTION", "CODE", "OBJECT", "BEGIN TIME", "END TIME"]
    sizes = [
        max([len(alarm.item) for alarm in alarms], default=0),
        max([len(alarm.description) for alarm in alarms], default=0),
        max([len(alarm.code) for alarm in alarms], default=0),
        max([len(alarm.object) for alarm in alarms], default=0),
        max([len(alarm.begintime) for alarm in alarms], default=0),
        max([len(alarm.endtime) for alarm in alarms], default=0),
    ]

    for i in range(len(cols)):
        max_size = max(len(cols[i]), sizes[i])
        cols[i] = cols[i].ljust(max_size)
        sizes[i] = max_size

    for alarm in alarms:
        alarm = replace(alarm, item=alarm.item.ljust(sizes[0]))
        alarm = replace(alarm, description=alarm.description.ljust(sizes[1]))
        alarm = replace(alarm, code=alarm.code.ljust(sizes[2]))
        alarm = replace(alarm, object=alarm.object.ljust(sizes[3]))
        alarm = replace(alarm, begintime=alarm.begintime.ljust(sizes[4]))
        alarm = replace(alarm, endtime=alarm.endtime.ljust(sizes[5]))

    table = []

    columns = build_alarm_table_header_lines(cols=cols)
    rows = build_alarm_table_rows(alarms=alarms)

    table.extend(columns)
    table.extend(rows)

    return table


def build_datacom_alarm_table(raw_alarms: list[str]) -> list[str]:
    if not raw_alarms:
        return [NO_ALARM_LABEL]

    alarms: list[DatacomAlarm] = []

    for raw_alarm in raw_alarms:
        alarm = raw_alarm.strip()
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
            DatacomAlarm(
                type=type,
                source_value=source_value,
                name=name,
                info=info,
                time=time,
                unstable=unstable,
                severity=severity,
            )
        )

    cols = ["TYPE", "SOURCE VALUE", "NAME", "INFO", "TIME", "UNSTABLE", "SEVERITY"]
    sizes = [
        max([len(alarm.type) for alarm in alarms], default=0),
        max([len(alarm.source_value) for alarm in alarms], default=0),
        max([len(alarm.name) for alarm in alarms], default=0),
        max([len(alarm.info) for alarm in alarms], default=0),
        max([len(alarm.time) for alarm in alarms], default=0),
        max([len(alarm.unstable) for alarm in alarms], default=0),
        max([len(alarm.severity) for alarm in alarms], default=0),
    ]

    for i in range(len(cols)):
        max_size = max(len(cols[i]), sizes[i])
        cols[i] = cols[i].ljust(max_size)
        sizes[i] = max_size

    for alarm in alarms:
        alarm = replace(alarm, type=alarm.type.ljust(sizes[0]))
        alarm = replace(alarm, source_value=alarm.source_value.ljust(sizes[1]))
        alarm = replace(alarm, name=alarm.name.ljust(sizes[2]))
        alarm = replace(alarm, info=alarm.info.ljust(sizes[3]))
        alarm = replace(alarm, time=alarm.time.ljust(sizes[4]))
        alarm = replace(alarm, unstable=alarm.unstable.ljust(sizes[5]))
        alarm = replace(alarm, severity=alarm.severity.ljust(sizes[6]))

    table = []

    columns = build_alarm_table_header_lines(cols=cols)
    rows = build_alarm_table_rows(alarms=alarms)

    table.extend(columns)
    table.extend(rows)

    return table
