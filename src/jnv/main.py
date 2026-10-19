import curses

from .clients.ssh import SSHClient
from .clients.telnet import TelnetClient
from .constants import CMD_ONU_ALARMS, CMD_PON_ALARMS, COMMANDS, OLTS
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
        try:
            client.connect()
        except Exception as exc:
            try:
                client.close()
            except Exception:
                pass
            ui.show_result(
                f"Falha ao conectar em {olt}",
                [
                    "Não foi possível estabelecer a conexão SSH:",
                    "",
                    str(exc),
                ],
            )
            return None, None, False
        return client, DatacomOLT(ssh_client=client), True

    if FiberhomeOLT.is_telnet_olt(olt):
        hostname = FiberhomeOLT.OLT_TELNET_HOSTNAMES[olt]
        client = TelnetClient(hostname=hostname)

        ui.show_loading([f"OLT: {olt}", f"Conectando via Telnet a {hostname}..."])
        try:
            client.connect()
        except Exception as exc:
            try:
                client.close()
            except Exception:
                pass
            ui.show_result(
                f"Falha ao conectar em {olt}",
                [
                    "Não foi possível estabelecer a conexão Telnet:",
                    "",
                    str(exc),
                ],
            )
            return None, None, False
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
            while True:
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
                if isinstance(olt_device, FiberhomeOLT):
                    available_pons = olt_device.get_pons(slot)
                else:
                    available_pons = olt_device.get_pons()

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
                                lines = olt_device.run_pon_alarms(slot, pon)
                            else:
                                lines = olt_device.run_pon_alarms()
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
                            lines = olt_device.run_onu_alarms(
                                slot=slot, pon=pon, onu=onu["id"]
                            )
                            ui.show_result(
                                f"{description} — {olt} / {slot} / {pon} "
                                f"/ {onu['label']}",
                                lines,
                            )
                            continue

                        continue
        finally:
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass


def run() -> None:
    curses.wrapper(main)
    print("Programa encerrado.")


if __name__ == "__main__":
    run()
