import re
from dataclasses import replace

from jnv_cli.types.alarms import DatacomAlarm, FiberhomeONUAlarm, FiberhomePONAlarm
from jnv_cli.utils import NO_ALARM_LABEL, NONE_LABEL


def build_fiberhome_pon_alarms(raw_lines: list[str]) -> list[str]:
    if not raw_lines:
        return [NO_ALARM_LABEL]

    alarms = []

    for raw_line in raw_lines:
        line = raw_line.strip().removesuffix(".")
        parts = line.split()

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
        status_match = STATUS_RE.search(string=line)
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

    max_slot = max([len(alarm.slot) for alarm in alarms], default=0)
    max_pon = max([len(alarm.pon) for alarm in alarms], default=0)
    max_onu = max([len(alarm.onu) for alarm in alarms], default=0)
    max_status = max([len(alarm.status) for alarm in alarms], default=0)

    h1 = "SLOT"
    h2 = "PON"
    h3 = "ONU"
    h4 = "STATUS"

    if max_slot > len(h1):
        h1 = h1.ljust(max_slot)
    else:
        max_slot = len(h1)

    if max_pon > len(h2):
        h2 = h2.ljust(max_pon)
    else:
        max_pon = len(h2)

    if max_onu > len(h3):
        h3 = h3.ljust(max_onu)
    else:
        max_onu = len(h3)

    if max_status > len(h4):
        h4 = h4.ljust(max_status)
    else:
        max_status = len(h4)

    alarms = [replace(alarm, slot=alarm.slot.ljust(max_slot)) for alarm in alarms]
    alarms = [replace(alarm, pon=alarm.pon.ljust(max_pon)) for alarm in alarms]
    alarms = [replace(alarm, onu=alarm.onu.ljust(max_onu)) for alarm in alarms]
    alarms = [replace(alarm, status=alarm.status.ljust(max_status)) for alarm in alarms]

    hs = f"{h1}   {h2}   {h3}   {h4}"
    dashes = "-" * len(hs)

    output = []
    output.append(hs)
    output.append(dashes)

    for alarm in alarms:
        output.append(f"{alarm.slot}   {alarm.pon}   {alarm.onu}   {alarm.status}")

    return output


def build_fiberhome_onu_alarms(raw_lines: list[str]) -> list[str]:
    if not raw_lines:
        return [NO_ALARM_LABEL]

    alarms = []

    for raw_line in raw_lines:
        line = raw_line.strip()
        parts = line.split()

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
        time_match = TIME_RE.findall(string=line)
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

    max_item = max([len(alarm.item) for alarm in alarms], default=0)
    max_description = max([len(alarm.description) for alarm in alarms], default=0)
    max_code = max([len(alarm.code) for alarm in alarms], default=0)
    max_object = max([len(alarm.object) for alarm in alarms], default=0)
    max_begintime = max([len(alarm.begintime) for alarm in alarms], default=0)
    max_endtime = max([len(alarm.endtime) for alarm in alarms], default=0)

    h1 = "ITEM"
    h2 = "DESCRIPTION"
    h3 = "CODE"
    h4 = "OBJECT"
    h5 = "BEGIN TIME"
    h6 = "END TIME"

    if max_item > len(h1):
        h1 = h1.ljust(max_item)
    else:
        max_item = len(h1)

    if max_description > len(h2):
        h2 = h2.ljust(max_description)
    else:
        max_description = len(h2)

    if max_code > len(h3):
        h3 = h3.ljust(max_code)
    else:
        max_code = len(h3)

    if max_object > len(h4):
        h4 = h4.ljust(max_object)
    else:
        max_object = len(h4)

    if max_begintime > len(h5):
        h5 = h5.ljust(max_begintime)
    else:
        max_begintime = len(h5)

    if max_endtime > len(h6):
        h6 = h6.ljust(max_endtime)
    else:
        max_endtime = len(h6)

    alarms = [replace(alarm, item=alarm.item.ljust(max_item)) for alarm in alarms]
    alarms = [
        replace(alarm, description=alarm.description.ljust(max_description))
        for alarm in alarms
    ]
    alarms = [replace(alarm, code=alarm.code.ljust(max_code)) for alarm in alarms]
    alarms = [replace(alarm, object=alarm.object.ljust(max_object)) for alarm in alarms]
    alarms = [
        replace(alarm, begintime=alarm.begintime.ljust(max_begintime))
        for alarm in alarms
    ]
    alarms = [
        replace(alarm, endtime=alarm.endtime.ljust(max_endtime)) for alarm in alarms
    ]

    hs = f"{h1}   {h2}   {h3}   {h4}   {h5}   {h6}"
    dashes = "-" * len(hs)

    output = []
    output.append(hs)
    output.append(dashes)

    for alarm in alarms:
        output.append(
            f"{alarm.item}   {alarm.description}   {alarm.code}   {alarm.object}   {alarm.begintime}   {alarm.endtime}"
        )

    return output


def build_datacom_alarms(raw_lines: list[str]) -> list[str]:
    if not raw_lines:
        return [NO_ALARM_LABEL]

    alarms = []

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
