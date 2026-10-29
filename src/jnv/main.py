import curses

from .clients.ssh_client import SSHClient
from .clients.telnet_client import TelnetClient
from .constants import (
    ALARM_FILTERS,
    ALARM_FILTERS_FIBERHOME,
    COMMANDS,
    OLT_PONS,
    OLTS,
)
from .olts.datacom_olt import DatacomOLT
from .olts.fiberhome_olt import FiberhomeOLT
from .ui import UI


def _open_connection_for(
    ui: UI, olt: str
) -> tuple[SSHClient | TelnetClient | None, DatacomOLT | FiberhomeOLT | None, bool]:
    if DatacomOLT.is_ssh_olt(olt):
        hostname = DatacomOLT.OLT_SSH_HOSTNAMES[olt]
        ui.show_loading([f"OLT: {olt}", f"Conectando via SSH a {hostname}..."])
        client = SSHClient(hostname=hostname)
        return client, DatacomOLT(ssh_client=client), True

    if FiberhomeOLT.is_telnet_olt(olt):
        hostname = FiberhomeOLT.OLT_TELNET_HOSTNAMES[olt]
        ui.show_loading([f"OLT: {olt}", f"Conectando via Telnet a {hostname}..."])
        client = TelnetClient(hostname=hostname)
        return client, FiberhomeOLT(telnet_client=client), True

    ui.show_result(
        f"Falha ao conectar em {olt}",
        ["Tipo de OLT não reconhecido ou sem suporte de conexão."],
    )
    return None, None, False


def _onu_label(olt_device: DatacomOLT | FiberhomeOLT, onu: dict) -> str:
    if isinstance(olt_device, FiberhomeOLT):
        return f"{onu['label']} — {onu['status']}"
    return (
        f"{onu['label']} — {onu['serial_number']} — "
        f"{onu['onu_state']} — {onu['onu_name']}"
    )


def _run_onu_alarms(
    olt_device: DatacomOLT | FiberhomeOLT, slot: str, pon: str, onu: dict
) -> list[str]:
    if isinstance(olt_device, FiberhomeOLT):
        return olt_device.run_onu_alarms(slot=slot, pon=pon, onu=onu["id"])
    return olt_device.run_onu_alarms(pon=pon, onu=onu["id"])


def _filter_fiberhome_onus(onus: list[dict], filter_code: str | None) -> list[dict]:
    if filter_code is None:
        return onus
    if filter_code == "Active":
        return [o for o in onus if o["status"].lower() == "active"]
    if filter_code == "Inactive":
        return [o for o in onus if o["status"].lower() == "inactive"]
    if filter_code == "Link loss":
        return [o for o in onus if o["status"].lower() == "link loss"]
    if filter_code == "Power down":
        return [o for o in onus if o["status"].lower() == "power down"]
    return onus


def main(stdscr: curses.window) -> None:
    curses.curs_set(0)
    stdscr.keypad(True)

    ui = UI(stdscr)
    olts = list(OLTS.keys())
    command_labels = [c for c in COMMANDS]

    last_olt_idx = 0
    last_slot_idx = 0
    last_pon_idx = 0
    last_cmd_idx = 0
    last_filter_idx = 0
    last_onu_idx = 0

    while True:
        idx = ui.select_menu(
            "Selecione a OLT", olts, can_exit=False, default=last_olt_idx
        )
        if idx is None:
            continue
        if idx != last_olt_idx:
            last_slot_idx = 0
            last_pon_idx = 0
            last_filter_idx = 0
            last_onu_idx = 0
        last_olt_idx = idx
        olt = olts[idx]

        client, olt_device, ok = _open_connection_for(ui, olt)
        if not ok or olt_device is None:
            continue

        try:
            slots = OLTS[olt]
            single_slot = len(slots) == 1

            while True:
                if single_slot:
                    slot = slots[0]
                else:
                    idx = ui.select_menu(
                        "Selecione o SLOT",
                        slots,
                        back=True,
                        context=[f"OLT: {olt}"],
                        default=last_slot_idx,
                    )
                    if idx is None:
                        break
                    if idx != last_slot_idx:
                        last_pon_idx = 0
                        last_onu_idx = 0
                    last_slot_idx = idx
                    slot = slots[idx]

                available_pons = OLT_PONS[olt][slot]

                while True:
                    idx = ui.select_menu(
                        "Selecione a PON",
                        available_pons,
                        back=True,
                        context=[f"OLT: {olt}", f"SLOT: {slot}"],
                        default=last_pon_idx,
                    )
                    if idx is None:
                        break
                    if idx != last_pon_idx:
                        last_onu_idx = 0
                    last_pon_idx = idx
                    pon = available_pons[idx]

                    while True:
                        idx = ui.select_menu(
                            "Selecione o comando",
                            command_labels,
                            back=True,
                            context=[
                                f"OLT: {olt}",
                                f"SLOT: {slot}",
                                f"PON: {pon}",
                            ],
                            default=last_cmd_idx,
                        )
                        if idx is None:
                            break
                        last_cmd_idx = idx

                        command = COMMANDS[idx]

                        ctx_base = [
                            f"OLT: {olt}",
                            f"SLOT: {slot}",
                            f"PON: {pon}",
                            f"Comando: {command}",
                        ]

                        if command == "Consultar alarmes da PON":
                            ui.show_loading(ctx_base)
                            if isinstance(olt_device, FiberhomeOLT):
                                lines = olt_device.run_pon_alarms(slot=slot, pon=pon)
                            else:
                                lines = olt_device.run_pon_alarms(pon=pon)
                            ui.show_result(
                                f"{command} — {olt} / {slot} / {pon}",
                                lines,
                            )
                            continue

                        if command == "Consultar alarmes das ONUs":
                            ui.show_loading(ctx_base)
                            onus = olt_device.get_onus(slot, pon)
                            if not onus:
                                ui.show_result(
                                    f"{command} — {olt} / {slot} / {pon}",
                                    ["Nenhuma ONU encontrada nesta PON."],
                                )
                                continue

                            if isinstance(olt_device, DatacomOLT):
                                pon_alarms_cache: list[str] | None = None

                                while True:
                                    max_code_len = max(
                                        (
                                            len(code)
                                            for code, _ in ALARM_FILTERS
                                            if code
                                        ),
                                        default=0,
                                    )
                                    filter_labels = [
                                        label
                                        if code is None
                                        else f"{code.ljust(max_code_len)} — {label}"
                                        for code, label in ALARM_FILTERS
                                    ]
                                    idx_filter = ui.select_menu(
                                        "Selecione o filtro de alarme",
                                        filter_labels,
                                        back=True,
                                        context=ctx_base,
                                        default=last_filter_idx,
                                    )
                                    if idx_filter is None:
                                        break
                                    if idx_filter != last_filter_idx:
                                        last_onu_idx = 0
                                    last_filter_idx = idx_filter

                                    filter_code, filter_label = ALARM_FILTERS[
                                        idx_filter
                                    ]

                                    if filter_code is None:
                                        filtered_onus = onus
                                    else:
                                        if pon_alarms_cache is None:
                                            ui.show_loading(
                                                ctx_base + [f"Filtro: {filter_label}"]
                                            )
                                            pon_alarms_cache = (
                                                olt_device.run_pon_alarms(pon=pon)
                                            )
                                        alarm_onu_ids = (
                                            olt_device.get_onu_ids_with_alarm(
                                                pon_alarms_cache, filter_code
                                            )
                                        )
                                        filtered_onus = [
                                            o
                                            for o in onus
                                            if (o["id"] - 1) in alarm_onu_ids
                                        ]

                                    if not filtered_onus:
                                        ui.show_result(
                                            f"{command} — {olt} / {slot} "
                                            f"/ {pon} / {filter_code}",
                                            [
                                                f"Nenhuma ONU nesta PON com o filtro '{filter_code}'."
                                            ],
                                        )
                                        continue

                                    labels = [
                                        _onu_label(olt_device, o) for o in filtered_onus
                                    ]
                                    filter_ctx = ctx_base + [f"Filtro: {filter_label}"]

                                    while True:
                                        idx_onu = ui.select_menu(
                                            f"Selecione a ONU — {filter_label}",
                                            labels,
                                            back=True,
                                            context=filter_ctx,
                                            default=last_onu_idx,
                                        )
                                        if idx_onu is None:
                                            break
                                        last_onu_idx = idx_onu

                                        onu = filtered_onus[idx_onu]
                                        ui.show_loading(
                                            filter_ctx + [f"ONU: {onu['label']}"]
                                        )
                                        lines = _run_onu_alarms(
                                            olt_device, slot, pon, onu
                                        )
                                        ui.show_result(
                                            f"{command} — {olt} / {slot} "
                                            f"/ {pon} / {onu['label']}",
                                            lines,
                                        )

                            elif isinstance(olt_device, FiberhomeOLT):
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
                                    idx_filter = ui.select_menu(
                                        "Selecione o filtro de status",
                                        filter_labels,
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

                                    filtered_onus = _filter_fiberhome_onus(
                                        onus, filter_code
                                    )

                                    if not filtered_onus:
                                        ui.show_result(
                                            f"{command} — {olt} / {slot} "
                                            f"/ {pon} / {filter_label}",
                                            [
                                                f"Nenhuma ONU nesta PON com o filtro '{filter_code}'."
                                            ],
                                        )
                                        continue

                                    labels = [
                                        _onu_label(olt_device, o) for o in filtered_onus
                                    ]
                                    filter_ctx = ctx_base + [f"Filtro: {filter_label}"]

                                    while True:
                                        idx_onu = ui.select_menu(
                                            f"Selecione a ONU — {filter_label}",
                                            labels,
                                            back=True,
                                            context=filter_ctx,
                                            default=last_onu_idx,
                                        )
                                        if idx_onu is None:
                                            break
                                        last_onu_idx = idx_onu

                                        onu = filtered_onus[idx_onu]
                                        ui.show_loading(
                                            filter_ctx + [f"ONU: {onu['label']}"]
                                        )
                                        lines = _run_onu_alarms(
                                            olt_device, slot, pon, onu
                                        )
                                        ui.show_result(
                                            f"{command} — {olt} / {slot} "
                                            f"/ {pon} / {onu['label']}",
                                            lines,
                                        )

                            continue

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
