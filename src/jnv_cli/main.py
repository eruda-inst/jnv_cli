import curses

from jnv_cli.clients.ssh_client import SSHClient
from jnv_cli.clients.telnet_client import TelnetClient
from jnv_cli.constants import (
    ALARM_FILTERS,
    COMMANDS,
    FIBERHOME_ALARM_FILTER_LABELS,
    FIBERHOME_ALARM_FILTERS,
    OLT_PONS,
    OLTS,
    SERIAL_FILTER_SENTINEL,
)
from jnv_cli.olts.datacom_olt import DatacomOLT
from jnv_cli.olts.fiberhome_olt import FiberhomeOLT
from jnv_cli.tui import TUI
from jnv_cli.utils import join_values, logger


def _open_connection(
    tui: TUI, olt_label: str
) -> tuple[SSHClient | TelnetClient | None, DatacomOLT | FiberhomeOLT | None]:
    if DatacomOLT.is_ssh_olt(olt=olt_label):
        hostname = DatacomOLT.OLT_SSH_HOSTNAMES[olt_label]
        tui.show_loading(
            context=[f"OLT: {olt_label}", f"Conectando via SSH a {hostname}..."]
        )
        client = SSHClient(hostname=hostname)
        return client, DatacomOLT(ssh_client=client)

    if FiberhomeOLT.is_telnet_olt(olt_label):
        hostname = FiberhomeOLT.OLT_TELNET_HOSTNAMES[olt_label]
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
        # --- OLT ---
        idx = tui.select_menu(
            question="Selecione a OLT",
            options=olt_labels,
            can_exit=False,
            default=last_olt_idx,
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
                # --- SLOT ---
                if single_slot:
                    slot_label = slots[0]
                else:
                    idx = tui.select_menu(
                        question="Selecione o SLOT",
                        options=slots,
                        back=True,
                        context=[f"OLT: {olt_label}"],
                        default=last_slot_idx,
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
                    # --- PON ---
                    idx = tui.select_menu(
                        question="Selecione a PON",
                        options=available_pons,
                        back=True,
                        context=[f"OLT: {olt_label}", f"SLOT: {slot_label}"],
                        default=last_pon_idx,
                    )
                    if idx is None:
                        break
                    if idx != last_pon_idx:
                        last_onu_idx = 0
                    last_pon_idx = idx
                    pon_label = available_pons[idx]

                    while True:
                        # --- Command ---
                        idx = tui.select_menu(
                            question="Selecione o comando",
                            options=COMMANDS,
                            back=True,
                            context=[
                                f"OLT: {olt_label}",
                                f"SLOT: {slot_label}",
                                f"PON: {pon_label}",
                            ],
                            default=last_cmd_idx,
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

                        # --- PON alarms ---
                        if command_label == "Consultar alarmes da PON":
                            tui.show_loading(context=ctx_base)
                            if isinstance(selected_olt, FiberhomeOLT):
                                lines = selected_olt.run_pon_alarms(
                                    slot=slot_label, pon=pon_label
                                )
                            else:
                                lines = selected_olt.run_pon_alarms(pon=pon_label)
                            tui.show_result(
                                title=(
                                    f"{command_label} — {olt_label} / "
                                    f"{slot_label} / {pon_label}"
                                ),
                                lines=lines,
                            )
                            continue

                        # --- ONU alarms ---
                        if command_label != "Consultar alarmes das ONUs":
                            # Comando desconhecido: ignora
                            continue

                        tui.show_loading(context=ctx_base)
                        if isinstance(selected_olt, DatacomOLT):
                            onus = selected_olt.get_onus(pon=pon_label)
                        else:
                            onus = selected_olt.get_onus(slot=slot_label, pon=pon_label)

                        if not onus or onus == ["(Sem alarmes)"]:
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
                                max_code_len = max(
                                    (
                                        len(code)
                                        for code, _ in ALARM_FILTERS
                                        if code and code != SERIAL_FILTER_SENTINEL
                                    ),
                                    default=0,
                                )
                                filter_labels = [
                                    label
                                    if code is None or code == SERIAL_FILTER_SENTINEL
                                    else join_values(
                                        values=[code.ljust(max_code_len), label]
                                    )
                                    for code, label in ALARM_FILTERS
                                ]
                                idx_filter = tui.select_menu(
                                    question="Selecione o filtro de alarme",
                                    options=filter_labels,
                                    back=True,
                                    context=ctx_base,
                                    default=last_filter_idx,
                                )
                                if idx_filter is None:
                                    break
                                if idx_filter != last_filter_idx:
                                    last_onu_idx = 0
                                last_filter_idx = idx_filter

                                filter_code, filter_label = ALARM_FILTERS[idx_filter]

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
                                        if serial_query in o["serial_number"].lower()  # type: ignore
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
                                        pon_alarms_cache = selected_olt.run_pon_alarms(
                                            pon=pon_label
                                        )
                                    alarm_onu_ids = selected_olt.get_onu_ids_with_alarm(
                                        alarm_lines=pon_alarms_cache,
                                        alarm_code=filter_code,
                                    )
                                    filtered_onus = [
                                        o
                                        for o in onus
                                        if (o["id"] - 1) in alarm_onu_ids
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

                                filtered_onu_labels = [
                                    selected_olt.get_onu_label(onu=onu)  # type: ignore[arg-type]
                                    for onu in filtered_onus
                                ]
                                filter_ctx = ctx_base + [filter_ctx_line]

                                while True:
                                    # --- ONU (Datacom) ---
                                    idx_onu = tui.select_menu(
                                        question=f"Selecione a ONU — {onu_question_suffix}",
                                        options=filtered_onu_labels,
                                        back=True,
                                        context=filter_ctx,
                                        default=last_onu_idx,
                                    )
                                    if idx_onu is None:
                                        break
                                    last_onu_idx = idx_onu

                                    onu = filtered_onus[idx_onu]
                                    tui.show_loading(
                                        context=filter_ctx + [f"ONU: {onu['label']}"]
                                    )
                                    lines = selected_olt.run_onu_alarms(
                                        pon=pon_label,
                                        onu=str(onu["id"]),
                                    )
                                    tui.show_result(
                                        title=(
                                            f"{command_label} — {olt_label} / "
                                            f"{slot_label} / {pon_label} / "
                                            f"{onu['label']}"
                                        ),
                                        lines=lines,
                                    )

                        elif isinstance(selected_olt, FiberhomeOLT):
                            while True:
                                max_code_len = max(
                                    (
                                        len(code)
                                        for code, _ in FIBERHOME_ALARM_FILTERS
                                        if code and code != SERIAL_FILTER_SENTINEL
                                    )
                                )
                                max_label_len = max(
                                    len(label)
                                    for label in FIBERHOME_ALARM_FILTER_LABELS
                                    if label not in (None, SERIAL_FILTER_SENTINEL)
                                )
                                filter_count_map = selected_olt.get_filter_count_map(
                                    onus=onus  # type: ignore
                                )
                                filter_labels = [
                                    label
                                    if code is None or code == SERIAL_FILTER_SENTINEL
                                    else join_values(
                                        values=[
                                            code.ljust(max_code_len),
                                            label.ljust(max_label_len),
                                            f"{filter_count_map[code]:03d}",
                                        ]
                                    )
                                    for code, label in FIBERHOME_ALARM_FILTERS
                                ]
                                idx_filter = tui.select_menu(
                                    question="Selecione o filtro de status",
                                    options=filter_labels,
                                    back=True,
                                    context=ctx_base,
                                    default=last_filter_idx,
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
                                        if serial_query in o["serial_number"].lower()  # type: ignore
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
                                    filtered_onus = selected_olt.filter_onus(
                                        onus=onus,  # type: ignore[arg-type]
                                        filter_code=filter_code,
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

                                status_width = max(
                                    (len(o["status"]) for o in filtered_onus),  # type: ignore
                                    default=0,
                                )
                                labels = [
                                    selected_olt.get_onu_label(
                                        onu=onu,  # type: ignore
                                        status_width=status_width,
                                    )
                                    for onu in filtered_onus
                                ]
                                filter_ctx = ctx_base + [filter_ctx_line]

                                while True:
                                    # --- ONU (Fiberhome) ---
                                    idx_onu = tui.select_menu(
                                        question=(
                                            f"Selecione a ONU — {onu_question_suffix}"
                                        ),
                                        options=labels,
                                        back=True,
                                        context=filter_ctx,
                                        default=last_onu_idx,
                                    )
                                    if idx_onu is None:
                                        break
                                    last_onu_idx = idx_onu

                                    onu = filtered_onus[idx_onu]
                                    tui.show_loading(
                                        context=filter_ctx + [f"ONU: {onu['label']}"]
                                    )
                                    lines = selected_olt.run_onu_alarms(
                                        slot=slot_label,
                                        pon=pon_label,
                                        onu=onu["id"],
                                    )

                                    tui.show_result(
                                        title=(
                                            f"{command_label} — {olt_label} / "
                                            f"{slot_label} / {pon_label} / "
                                            f"{onu['label']}"
                                        ),
                                        lines=lines,
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
        logger.error(msg="Conexão encerrada por ociosidade.")
    except KeyboardInterrupt:
        logger.info(msg="Programa encerrado pelo usuário.")


if __name__ == "__main__":
    run()
