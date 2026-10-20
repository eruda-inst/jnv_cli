import curses

from .clients.ssh import SSHClient
from .clients.telnet import TelnetClient
from .constants import (
    CMD_ONU_ALARMS,
    CMD_PON_ALARMS,
    COMMANDS,
    OLT_PONS,
    OLTS,
)
from .olts.datacom import DatacomOLT
from .olts.fiberhome import FiberhomeOLT
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
        client.connect()
        return client, FiberhomeOLT(telnet_client=client), True

    ui.show_result(
        f"Falha ao conectar em {olt}",
        ["Tipo de OLT não reconhecido ou sem suporte de conexão."],
    )
    return None, None, False


def main(stdscr: curses.window) -> None:
    curses.curs_set(0)
    stdscr.keypad(True)

    ui = UI(stdscr)
    olts = list(OLTS.keys())
    command_labels = [f"{letter} - {description}" for letter, description in COMMANDS]

    while True:
        idx = ui.select_menu(
            "Selecione a OLT que você deseja acessar",
            olts,
            can_exit=False,
        )
        if idx is None:
            continue
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
                    )
                    if idx is None:
                        break
                    slot = slots[idx]

                ui.show_loading([f"OLT: {olt}", f"SLOT: {slot}", "Buscando PONs..."])
                available_pons = OLT_PONS[olt]

                while True:
                    idx = ui.select_menu(
                        "Selecione a PON",
                        available_pons,
                        back=True,
                        context=[f"OLT: {olt}", f"SLOT: {slot}"],
                    )
                    if idx is None:
                        break
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
                        )
                        if idx is None:
                            break

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
                                lines = olt_device.run_pon_alarms(slot=slot, pon=pon)  # type: ignore
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

                            labels = [o["label"] for o in onus]
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
                            )
                            if idx_onu is None:
                                continue

                            onu = onus[idx_onu]
                            ui.show_loading(ctx_base + [f"ONU: {onu['label']}"])
                            lines = olt_device.run_onu_alarms(pon=pon, onu=onu["id"])
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
