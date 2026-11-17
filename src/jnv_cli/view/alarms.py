import re
from collections.abc import Sequence
from dataclasses import asdict
from typing import Any

from jnv_cli.types.alarms import (
    Alarms,
    DatacomAlarm,
    FiberhomeONUAlarm,
    FiberhomePONAlarm,
)
from jnv_cli.utils import NO_ALARM_LABEL, NONE_LABEL

_COLUMN_SEPARATOR = " | "
_HORIZONTAL_LINE_CHARACTER = "-"
_FIBERHOME_PON_STATUS_RE = re.compile(pattern=r"active|inactive|power down|link loss")
_FIBERHOME_ONU_TIME_RE = re.compile(pattern=r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
_DATACOM_INFO_RE = re.compile(
    pattern=(
        r"ONU Loss of signal|Signal loss of ONU|Receive dying gasp of ONU|Deactivate failure of ONU|Drift of (?:the )?window of ONU|Loss of GEM channel delineation|Loss of acknowledge with ONU|Loss of PLOAM for ONU|Loss of burst of ONU|Loss of frame of ONU|Loss of OMCC channel|Loss of PLOAM channel|Link mismatch of ONU|Auto provisioning fail|ONU auto provisioning fail|ONU down|The ONU has an internal problem/defect or ONU was disconnected from the PON link|ONU equipment failure|ONU password mismatch|ONU self-test failure|Physical equipment error of ONU|Remote defect indication of ONU|Signal degraded of ONU|Signal fail of ONU|Start-up failure of ONU|Transmission interference warning of ONU"
    )
)
_DATACOM_TIME_RE = re.compile(pattern=r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC[\+-]\d")


def _build_alarm_table_header_lines(cols: Sequence[str]) -> list[str]:
    header = _COLUMN_SEPARATOR.join(cols)
    return [header, _HORIZONTAL_LINE_CHARACTER * len(header)]


def _build_alarm_table_rows(alarms: list[dict[str, Any]]) -> list[str]:
    return [_COLUMN_SEPARATOR.join(alarm.values()) for alarm in alarms]


def _build_alarm_table(alarms: Alarms, cols: list[str]) -> list[str]:
    alarms_dict = [asdict(alarm) for alarm in alarms]
    sizes = []
    map = {}

    for alarm in alarms_dict:
        for key, value in alarm.items():
            if map.get(key) is None:
                map[key] = []
            map[key].append(value)

    for key, values in map.items():
        sizes.append(max([len(str(value)) for value in values], default=0))

    for i in range(len(cols)):
        max_size = max(len(cols[i]), sizes[i])
        cols[i] = cols[i].ljust(max_size)
        sizes[i] = max_size

    for alarm in alarms_dict:
        for i, key in enumerate(alarm):
            alarm[key] = alarm[key].ljust(sizes[i])

    table = []

    columns = _build_alarm_table_header_lines(cols=cols)
    rows = _build_alarm_table_rows(alarms=alarms_dict)

    table.extend(columns)
    table.extend(rows)

    return table


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

        status_match = _FIBERHOME_PON_STATUS_RE.search(string=alarm)
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

    alarms = sorted(alarms, key=lambda alarm: alarm.status, reverse=True)

    cols = ["SLOT", "PON", "ONU", "STATUS"]

    return _build_alarm_table(alarms=alarms, cols=cols)


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

        time_match = _FIBERHOME_ONU_TIME_RE.findall(string=alarm)
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

    alarms = sorted(alarms, key=lambda alarm: alarm.begintime, reverse=True)

    cols = ["ITEM", "DESCRIPTION", "CODE", "OBJECT", "BEGIN TIME", "END TIME"]

    return _build_alarm_table(alarms=alarms, cols=cols)


def build_datacom_alarm_table(raw_alarms: list[str]) -> list[str]:
    if not raw_alarms:
        return [NO_ALARM_LABEL]

    alarms: list[DatacomAlarm] = []

    for raw_alarm in raw_alarms:
        alarm = raw_alarm.strip()
        parts = alarm.split()

        type_ = NONE_LABEL
        source_value = NONE_LABEL
        name = NONE_LABEL
        info = NONE_LABEL
        time = NONE_LABEL
        unstable = NONE_LABEL
        severity = NONE_LABEL

        if len(parts) >= 1:
            type_ = parts[0]

        if len(parts) >= 2:
            source_value = parts[1]
            severity = parts[-1]

        if len(parts) >= 3:
            name = parts[2]
            unstable = parts[-2]

        match_info = _DATACOM_INFO_RE.search(string=alarm)
        if match_info is not None:
            info = match_info.group()

        match_time = _DATACOM_TIME_RE.search(string=alarm)
        if match_time is not None:
            time = match_time.group()

        alarms.append(
            DatacomAlarm(
                type=type_,
                source_value=source_value,
                name=name,
                info=info,
                time=time,
                unstable=unstable,
                severity=severity,
            )
        )

    alarms = sorted(alarms, key=lambda alarm: alarm.time, reverse=True)

    cols = ["TYPE", "SOURCE VALUE", "NAME", "INFO", "TIME", "UNSTABLE", "SEVERITY"]

    return _build_alarm_table(alarms=alarms, cols=cols)
