import curses

from .clients.ssh_client import SSHClient
from .clients.telnet_client import TelnetClient
from .constants import (
    CMD_ONU_ALARMS,
    CMD_PON_ALARMS,
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
        client = SSHClient(hostname=hostname)
        ui.show_loading([f"OLT: {olt}", f"Conectando via SSH a {hostname}..."])
        return client, DatacomOLT(ssh_client=client), True

    if FiberhomeOLT.is_telnet_olt(olt):
        hostname = FiberhomeOLT.OLT_TELNET_HOSTNAMES[olt]
        client = TelnetClient(hostname=hostname)
        ui.show_loading([f"OLT: {olt}", f"Conectando via Telnet a {hostname}..."])
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


def main(stdscr: curses.window) -> None:
    curses.curs_set(0)
    stdscr.keypad(True)

    ui = UI(stdscr)
    olts = list(OLTS.keys())
    command_labels = [f"{letter} - {description}" for letter, description in COMMANDS]

    last_olt_idx = 0
    last_slot_idx = 0
    last_pon_idx = 0
    last_cmd_idx = 0
    last_onu_idx = 0

    while True:
        idx = ui.select_menu(
            "Selecione a OLT que você deseja acessar",
            olts,
            can_exit=False,
            default=last_olt_idx,
        )
        if idx is None:
            continue
        if idx != last_olt_idx:
            last_slot_idx = 0
            last_pon_idx = 0
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
                        context=[f"OLT selecionada: {olt}"],
                        default=last_slot_idx,
                    )
                    if idx is None:
                        break
                    if idx != last_slot_idx:
                        last_pon_idx = 0
                        last_onu_idx = 0
                    last_slot_idx = idx
                    slot = slots[idx]

                ui.show_loading([f"OLT: {olt}", f"SLOT: {slot}", "Buscando PONs..."])
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

                        letter, description = COMMANDS[idx]

                        ctx_base = [
                            f"OLT: {olt}",
                            f"SLOT: {slot}",
                            f"PON: {pon}",
                            f"Comando: {description}",
                        ]

                        if letter == CMD_PON_ALARMS:
                            ui.show_loading(ctx_base)
                            if isinstance(olt_device, FiberhomeOLT):
                                lines = olt_device.run_pon_alarms(slot=slot, pon=pon)
                            else:
                                lines = olt_device.run_pon_alarms(pon_number=pon)
                            ui.show_result(
                                f"{description} — {olt} / {slot} / {pon}",
                                lines,
                            )
                            continue

                        if letter == CMD_ONU_ALARMS:
                            ui.show_loading(ctx_base)
                            onus = olt_device.get_onus(slot, pon)
                            if not onus:
                                ui.show_result(
                                    f"{description} — {olt} / {slot} / {pon}",
                                    ["Nenhuma ONU encontrada nesta PON."],
                                )
                                continue

                            labels = [_onu_label(olt_device, o) for o in onus]

                            while True:
                                idx_onu = ui.select_menu(
                                    "Selecione a ONU",
                                    labels,
                                    back=True,
                                    context=[
                                        f"OLT: {olt}",
                                        f"SLOT: {slot}",
                                        f"PON: {pon}",
                                        f"Comando: {description}",
                                    ],
                                    default=last_onu_idx,
                                )
                                if idx_onu is None:
                                    break

                                last_onu_idx = idx_onu

                                onu = onus[idx_onu]
                                ui.show_loading(ctx_base + [f"ONU: {onu['label']}"])
                                lines = _run_onu_alarms(olt_device, slot, pon, onu)
                                ui.show_result(
                                    f"{description} — {olt} / {slot} / {pon} "
                                    f"/ {onu['label']}",
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
