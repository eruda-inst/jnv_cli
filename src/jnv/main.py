import curses

from jnv.clients.ssh_client import SSHClient
from jnv.clients.telnet_client import TelnetClient
from jnv.constants import (
    ALARM_FILTERS,
    ALARM_FILTERS_FIBERHOME,
    COMMANDS,
    OLT_PONS,
    OLTS,
)
from jnv.olts.datacom_olt import DatacomOLT
from jnv.olts.fiberhome_olt import FiberhomeOLT
from jnv.tui import TUI


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
                        onus = selected_olt.get_onus(pon=pon_label)
                        if not onus:
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
                                    (len(code) for code, _ in ALARM_FILTERS if code),
                                    default=0,
                                )
                                filter_labels = [
                                    label
                                    if code is None
                                    else f"{code.ljust(max_code_len)} — {label}"
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

                                if filter_code is None:
                                    filtered_onus = onus
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

                                if not filtered_onus:
                                    tui.show_result(
                                        title=(
                                            f"{command_label} — {olt_label} / "
                                            f"{slot_label} / {pon_label} / "
                                            f"{filter_code}"
                                        ),
                                        lines=[
                                            "Nenhuma ONU nesta PON com o filtro '{filter_code}'."
                                        ],
                                    )
                                    continue

                                filtered_onu_labels = [
                                    selected_olt.get_onu_label(onu=onu)  # type: ignore[arg-type]
                                    for onu in filtered_onus
                                ]
                                filter_ctx = ctx_base + [f"Filtro: {filter_label}"]

                                while True:
                                    # --- ONU (Datacom) ---
                                    idx_onu = tui.select_menu(
                                        question=(f"Selecione a ONU — {filter_label}"),
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
                                        for code, _ in ALARM_FILTERS_FIBERHOME
                                        if code
                                    ),
                                    default=0,
                                )
                                filter_labels = [
                                    label
                                    if code is None
                                    else f"{code.ljust(max_code_len)} — {label}"
                                    for code, label in ALARM_FILTERS_FIBERHOME
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

                                filter_code, filter_label = ALARM_FILTERS_FIBERHOME[
                                    idx_filter
                                ]

                                filtered_onus = selected_olt.filter_onus(
                                    onus=onus,  # type: ignore[arg-type]
                                    filter_code=filter_code,
                                )

                                if not filtered_onus:
                                    tui.show_result(
                                        title=(
                                            f"{command_label} — {olt_label} / "
                                            f"{slot_label} / {pon_label} / "
                                            f"{filter_label}"
                                        ),
                                        lines=[
                                            "Nenhuma ONU nesta PON com o filtro '{filter_code}'."
                                        ],
                                    )
                                    continue

                                labels = [
                                    selected_olt.get_onu_label(onu=onu)
                                    for onu in filtered_onus
                                ]
                                filter_ctx = ctx_base + [f"Filtro: {filter_label}"]

                                while True:
                                    # --- ONU (Fiberhome) ---
                                    idx_onu = tui.select_menu(
                                        question=(f"Selecione a ONU — {filter_label}"),
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
    except KeyboardInterrupt:
        print("Programa encerrado.")


if __name__ == "__main__":
    run()
