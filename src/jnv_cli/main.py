import curses

from jnv_cli.clients.ssh_client import SSHClient
from jnv_cli.clients.telnet_client import TelnetClient
from jnv_cli.olts.datacom_olt import (
    DATACOM_ALARM_FILTERS,
    DatacomOLT,
    get_datacom_onu_ids_with_alarm,
)
from jnv_cli.olts.fiberhome_olt import (
    FIBERHOME_ALARM_FILTERS,
    FiberhomeOLT,
    filter_fiberhome_onus_by_status,
)
from jnv_cli.tui import TUI
from jnv_cli.types.olt import OLTNames
from jnv_cli.utils import NO_ALARM_LABEL, SERIAL_FILTER_SENTINEL, count_alarms_by_filter
from jnv_cli.view.alarms import (
    build_datacom_alarm_table,
    build_fiberhome_onu_alarm_table,
    build_fiberhome_pon_alarm_table,
)
from jnv_cli.view.menus import build_filter_labels, build_onu_menu, build_order_menu

COMMANDS = ("Consultar alarmes das ONUs", "Consultar alarmes da PON")
OLTS = {
    OLTNames.ACIJA: [f"SLOT {i:03d}" for i in range(1, 4 + 1)],
    OLTNames.ITAITU: [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    OLTNames.JACOBINA_III: [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    OLTNames.LAGES_DO_BATATA: [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    OLTNames.NEWNET: [f"SLOT {i:03d}" for i in range(1, 7 + 1)],
    OLTNames.PALMEIRINHA: [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
    OLTNames.PARAISO: [f"SLOT {i:03d}" for i in range(1, 1 + 1)],
}
OLT_PONS = {
    OLTNames.ACIJA: {
        slot: [f"PON {i:03d}" for i in range(1, 16 + 1)]
        for slot in OLTS[OLTNames.ACIJA]
    },
    OLTNames.ITAITU: {
        slot: [f"PON {i:03d}" for i in range(1, 8 + 1)]
        for slot in OLTS[OLTNames.ITAITU]
    },
    OLTNames.JACOBINA_III: {
        slot: [f"PON {i:03d}" for i in range(1, 16 + 1)]
        for slot in OLTS[OLTNames.JACOBINA_III]
    },
    OLTNames.LAGES_DO_BATATA: {
        slot: [f"PON {i:03d}" for i in range(1, 16 + 1)]
        for slot in OLTS[OLTNames.LAGES_DO_BATATA]
    },
    OLTNames.NEWNET: {
        **{
            slot: [f"PON {i:03d}" for i in range(1, 8 + 1)]
            for slot in OLTS[OLTNames.NEWNET][:3]
        },
        **{
            slot: [f"PON {i:03d}" for i in range(1, 16 + 1)]
            for slot in OLTS[OLTNames.NEWNET][3:]
        },
    },
    OLTNames.PALMEIRINHA: {
        slot: [f"PON {i:03d}" for i in range(1, 8 + 1)]
        for slot in OLTS[OLTNames.PALMEIRINHA]
    },
    OLTNames.PARAISO: {
        slot: [f"PON {i:03d}" for i in range(1, 16 + 1)]
        for slot in OLTS[OLTNames.PARAISO]
    },
}


def _open_connection(
    tui: TUI, olt_label: OLTNames
) -> tuple[SSHClient | TelnetClient | None, DatacomOLT | FiberhomeOLT | None]:
    if DatacomOLT.is_datacom_olt(olt=olt_label):
        hostname = DatacomOLT.DATACOM_HOSTNAMES[olt_label]
        tui.show_loading(
            context=[f"OLT: {olt_label}", f"Conectando via SSH a {hostname}..."]
        )
        client = SSHClient(hostname=hostname)
        return client, DatacomOLT(ssh_client=client)

    if FiberhomeOLT.is_fiberhome_olt(olt_label):
        hostname = FiberhomeOLT.FIBERHOME_HOSTNAMES[olt_label]
        tui.show_loading(
            context=[f"OLT: {olt_label}", f"Conectando via Telnet a {hostname}..."]
        )
        client = TelnetClient(hostname=hostname)
        return client, FiberhomeOLT(telnet_client=client)

    tui.show_result(
        title=f"Falha ao conectar em {olt_label}",
        lines=["Tipo de OLT não reconhecido ou sem suporte de conexão."],
    )
    return None, None


def main(stdscr: curses.window) -> None:
    curses.curs_set(0)
    stdscr.keypad(True)

    tui = TUI(stdscr)
    olt_labels = tuple(OLTS.keys())

    last_olt_idx = 0
    last_slot_idx = 0
    last_pon_idx = 0
    last_cmd_idx = 0
    last_filter_idx = 0
    last_onu_idx = 0

    while True:
        header, olt_menu_labels = build_order_menu(labels=olt_labels)
        idx = tui.select_menu(
            question="Selecione a OLT",
            options=olt_menu_labels,
            can_exit=False,
            default=last_olt_idx,
            header=header,
        )
        if idx is None:
            continue
        if idx != last_olt_idx:
            last_slot_idx = 0
            last_pon_idx = 0
            last_filter_idx = 0
            last_onu_idx = 0
        last_olt_idx = idx
        olt_label = olt_labels[idx]

        client, selected_olt = _open_connection(tui=tui, olt_label=olt_label)
        if client is None or selected_olt is None:
            continue

        try:
            slots = OLTS[olt_label]
            single_slot = len(slots) == 1

            while True:
                if single_slot:
                    slot_label = slots[0]
                else:
                    slot_header, slot_menu_labels = build_order_menu(
                        labels=slots, column="SLOT", strip_prefix="SLOT "
                    )
                    idx = tui.select_menu(
                        question="Selecione o SLOT",
                        options=slot_menu_labels,
                        back=True,
                        context=[f"OLT: {olt_label}"],
                        default=last_slot_idx,
                        header=slot_header,
                    )
                    if idx is None:
                        break
                    if idx != last_slot_idx:
                        last_pon_idx = 0
                        last_onu_idx = 0
                    last_slot_idx = idx
                    slot_label = slots[idx]

                available_pons = OLT_PONS[olt_label][slot_label]

                while True:
                    pon_header, pon_menu_labels = build_order_menu(
                        labels=available_pons, column="PON", strip_prefix="PON "
                    )
                    idx = tui.select_menu(
                        question="Selecione a PON",
                        options=pon_menu_labels,
                        back=True,
                        context=[f"OLT: {olt_label}", f"SLOT: {slot_label}"],
                        default=last_pon_idx,
                        header=pon_header,
                    )
                    if idx is None:
                        break
                    if idx != last_pon_idx:
                        last_onu_idx = 0
                    last_pon_idx = idx
                    pon_label = available_pons[idx]

                    while True:
                        cmd_header, cmd_menu_labels = build_order_menu(
                            labels=COMMANDS, column="COMMAND"
                        )
                        idx = tui.select_menu(
                            question="Selecione o comando",
                            options=cmd_menu_labels,
                            back=True,
                            context=[
                                f"OLT: {olt_label}",
                                f"SLOT: {slot_label}",
                                f"PON: {pon_label}",
                            ],
                            default=last_cmd_idx,
                            header=cmd_header,
                        )
                        if idx is None:
                            break
                        last_cmd_idx = idx
                        command_label = COMMANDS[idx]

                        ctx_base = [
                            f"OLT: {olt_label}",
                            f"SLOT: {slot_label}",
                            f"PON: {pon_label}",
                            f"Comando: {command_label}",
                        ]

                        if command_label == "Consultar alarmes da PON":
                            tui.show_loading(context=ctx_base)
                            if isinstance(selected_olt, FiberhomeOLT):
                                raw_alarms = selected_olt.get_pon_alarms(
                                    slot=slot_label, pon=pon_label
                                )
                                alarms = build_fiberhome_pon_alarm_table(
                                    raw_alarms=raw_alarms
                                )
                            else:
                                raw_alarms = selected_olt.get_alarms(pon=pon_label)
                                alarms = build_datacom_alarm_table(
                                    raw_alarms=raw_alarms
                                )
                            tui.show_result(
                                title=(
                                    f"{command_label} — {olt_label} / "
                                    f"{slot_label} / {pon_label}"
                                ),
                                lines=alarms,
                            )
                            continue

                        if command_label != "Consultar alarmes das ONUs":
                            continue

                        tui.show_loading(context=ctx_base)
                        if isinstance(selected_olt, DatacomOLT):
                            onus = selected_olt.get_onus(pon=pon_label)
                        else:
                            onus = selected_olt.get_onus(slot=slot_label, pon=pon_label)

                        if not onus or onus == [NO_ALARM_LABEL]:
                            tui.show_result(
                                title=(
                                    f"{command_label} — {olt_label} / "
                                    f"{slot_label} / {pon_label}"
                                ),
                                lines=["Nenhuma ONU encontrada nesta PON."],
                            )
                            continue

                        if isinstance(selected_olt, DatacomOLT):
                            pon_alarms_cache: list[str] | None = None

                            while True:
                                raw_lines = selected_olt.get_alarms(pon=pon_label)
                                pon_alarms = build_datacom_alarm_table(raw_lines)
                                filter_header, filter_labels = build_filter_labels(
                                    filters=DATACOM_ALARM_FILTERS,
                                    count_map=count_alarms_by_filter(
                                        alarms=pon_alarms, filters=DATACOM_ALARM_FILTERS
                                    ),
                                    total=len(onus),
                                )
                                idx_filter = tui.select_menu(
                                    question="Selecione o filtro de alarme",
                                    options=filter_labels,
                                    back=True,
                                    context=ctx_base,
                                    default=last_filter_idx,
                                    header=filter_header,
                                )
                                if idx_filter is None:
                                    break
                                if idx_filter != last_filter_idx:
                                    last_onu_idx = 0
                                last_filter_idx = idx_filter

                                filter_code, filter_label = DATACOM_ALARM_FILTERS[
                                    idx_filter
                                ]

                                if filter_code == SERIAL_FILTER_SENTINEL:
                                    serial_input = tui.ask_input(
                                        question="Digite o serial number da ONU",
                                        context=ctx_base,
                                    )
                                    if serial_input is None or not serial_input.strip():
                                        continue
                                    serial_text = serial_input.strip()
                                    serial_query = serial_text.lower()
                                    filtered_onus = [
                                        o
                                        for o in onus
                                        if serial_query in o.serial.lower()  # type: ignore
                                    ]
                                    title_filter = f'Serial "{serial_text}"'
                                    filter_ctx_line = f'Serial: "{serial_text}"'
                                    onu_question_suffix = f'Serial "{serial_text}"'
                                    no_result_msg = f"Nenhuma ONU nesta PON com serial contendo '{serial_text}'."

                                elif filter_code is None:
                                    filtered_onus = onus
                                    title_filter = None
                                    filter_ctx_line = f"Filtro: {filter_label}"
                                    onu_question_suffix = filter_label
                                    no_result_msg = "Nenhuma ONU nesta PON."

                                else:
                                    if pon_alarms_cache is None:
                                        tui.show_loading(
                                            context=ctx_base
                                            + [f"Filtro: {filter_label}"]
                                        )
                                        raw_alarms = selected_olt.get_alarms(
                                            pon=pon_label
                                        )
                                        pon_alarms_cache = build_datacom_alarm_table(
                                            raw_alarms=raw_alarms
                                        )
                                    alarm_onu_ids = get_datacom_onu_ids_with_alarm(
                                        alarms=pon_alarms_cache,
                                        code=filter_code,
                                    )
                                    filtered_onus = [
                                        o for o in onus if o.id in alarm_onu_ids
                                    ]
                                    title_filter = filter_code
                                    filter_ctx_line = f"Filtro: {filter_label}"
                                    onu_question_suffix = filter_label
                                    no_result_msg = f"Nenhuma ONU nesta PON com o filtro '{filter_code}'."

                                if not filtered_onus:
                                    title = (
                                        f"{command_label} — {olt_label} / "
                                        f"{slot_label} / {pon_label}"
                                    )
                                    if title_filter:
                                        title = f"{title} / {title_filter}"
                                    tui.show_result(
                                        title=title,
                                        lines=[no_result_msg],
                                    )
                                    continue

                                header, filtered_onu_labels = build_onu_menu(
                                    onus=filtered_onus
                                )
                                filter_ctx = ctx_base + [filter_ctx_line]

                                while True:
                                    idx_onu = tui.select_menu(
                                        question=f"Selecione a ONU — {onu_question_suffix}",
                                        options=filtered_onu_labels,
                                        back=True,
                                        context=filter_ctx,
                                        default=last_onu_idx,
                                        header=header,
                                    )
                                    if idx_onu is None:
                                        break
                                    last_onu_idx = idx_onu

                                    onu = filtered_onus[idx_onu]
                                    tui.show_loading(
                                        context=filter_ctx + [f"ONU: {onu.label}"]
                                    )
                                    raw_alarms = selected_olt.get_alarms(
                                        pon=pon_label,
                                        onu=str(onu.id),
                                    )
                                    lines = build_datacom_alarm_table(
                                        raw_alarms=raw_alarms
                                    )
                                    tui.show_result(
                                        title=(
                                            f"{command_label} — {olt_label} / "
                                            f"{slot_label} / {pon_label} / "
                                            f"{onu.label}"
                                        ),
                                        lines=lines,
                                    )

                        elif isinstance(selected_olt, FiberhomeOLT):
                            while True:
                                raw_alarms = selected_olt.get_pon_alarms(
                                    pon=pon_label, slot=slot_label
                                )
                                pon_alarms = build_fiberhome_pon_alarm_table(
                                    raw_alarms=raw_alarms
                                )
                                filter_header, filter_labels = build_filter_labels(
                                    filters=FIBERHOME_ALARM_FILTERS,
                                    count_map=count_alarms_by_filter(
                                        alarms=pon_alarms,
                                        filters=FIBERHOME_ALARM_FILTERS,
                                    ),
                                    total=len(onus),
                                )
                                idx_filter = tui.select_menu(
                                    question="Selecione o filtro de status",
                                    options=filter_labels,
                                    back=True,
                                    context=ctx_base,
                                    default=last_filter_idx,
                                    header=filter_header,
                                )
                                if idx_filter is None:
                                    break
                                if idx_filter != last_filter_idx:
                                    last_onu_idx = 0
                                last_filter_idx = idx_filter

                                filter_code, filter_label = FIBERHOME_ALARM_FILTERS[
                                    idx_filter
                                ]

                                if filter_code == SERIAL_FILTER_SENTINEL:
                                    serial_input = tui.ask_input(
                                        question="Digite o serial number da ONU",
                                        context=ctx_base,
                                    )
                                    if serial_input is None or not serial_input.strip():
                                        continue
                                    serial_text = serial_input.strip()
                                    serial_query = serial_text.lower()
                                    filtered_onus = [
                                        o
                                        for o in onus
                                        if serial_query in o.serial.lower()  # type: ignore
                                    ]
                                    title_filter = f'Serial "{serial_text}"'
                                    filter_ctx_line = f'Serial: "{serial_text}"'
                                    onu_question_suffix = f'Serial "{serial_text}"'
                                    no_result_msg = (
                                        f"Nenhuma ONU nesta PON com serial "
                                        f"contendo '{serial_text}'."
                                    )

                                elif filter_code is None:
                                    filtered_onus = onus
                                    title_filter = None
                                    filter_ctx_line = f"Filtro: {filter_label}"
                                    onu_question_suffix = filter_label
                                    no_result_msg = "Nenhuma ONU nesta PON."

                                else:
                                    filtered_onus = filter_fiberhome_onus_by_status(
                                        onus=onus,  # type: ignore
                                        status=filter_code,
                                    )
                                    title_filter = filter_code
                                    filter_ctx_line = f"Filtro: {filter_label}"
                                    onu_question_suffix = filter_label
                                    no_result_msg = (
                                        f"Nenhuma ONU nesta PON com o filtro "
                                        f"'{filter_code}'."
                                    )

                                if not filtered_onus:
                                    title = (
                                        f"{command_label} — {olt_label} / "
                                        f"{slot_label} / {pon_label}"
                                    )
                                    if title_filter:
                                        title = f"{title} / {title_filter}"
                                    tui.show_result(
                                        title=title,
                                        lines=[no_result_msg],
                                    )
                                    continue

                                header, labels = build_onu_menu(onus=filtered_onus)
                                filter_ctx = ctx_base + [filter_ctx_line]

                                while True:
                                    idx_onu = tui.select_menu(
                                        question=(
                                            f"Selecione a ONU — {onu_question_suffix}"
                                        ),
                                        options=labels,
                                        back=True,
                                        context=filter_ctx,
                                        default=last_onu_idx,
                                        header=header,
                                    )
                                    if idx_onu is None:
                                        break
                                    last_onu_idx = idx_onu

                                    onu = filtered_onus[idx_onu]
                                    tui.show_loading(
                                        context=filter_ctx + [f"ONU: {onu.label}"]
                                    )
                                    raw_alarms = selected_olt.get_onu_alarms(
                                        slot=slot_label,
                                        pon=pon_label,
                                        onu=onu.id,
                                    )
                                    alarms = build_fiberhome_onu_alarm_table(
                                        raw_alarms=raw_alarms
                                    )
                                    tui.show_result(
                                        title=(
                                            f"{command_label} — {olt_label} / "
                                            f"{slot_label} / {pon_label} / "
                                            f"{onu.label}"
                                        ),
                                        lines=alarms,
                                    )

                        continue

                if single_slot:
                    break
        finally:
            if client is not None:
                client.close()


def run() -> None:
    try:
        curses.wrapper(main)
    except ConnectionResetError:
        print("Conexão encerrada por ociosidade.")
    except KeyboardInterrupt:
        print("Programa encerrado pelo usuário.")


if __name__ == "__main__":
    run()
