import curses
from collections.abc import Callable, Sequence
from string import ascii_letters, digits
from typing import ClassVar

from jnv_cli.types.colors import RGBColor
from jnv_cli.types.keys import Keys

TITLE = "JNV (Jacobina Network Viewer) v1.17.3"
CREDITS = "Desenvolvido pelo setor de inovação da Newnet"


class TUI:
    _MATT_BLUE_COLOR: ClassVar[RGBColor] = RGBColor(r=37, g=110, b=206)
    _ROYAL_BLUE_COLOR: ClassVar[RGBColor] = RGBColor(r=65, g=105, b=225)
    _CERULEAN_COLOR: ClassVar[RGBColor] = RGBColor(r=0, g=123, b=167)

    _CONFIRM_KEYS: ClassVar[tuple[Keys, ...]] = (
        Keys.KEY_ENTER,
        Keys.KEY_CTRL_LF,
        Keys.KEY_CTRL_CR,
    )
    _CANCEL_KEYS: ClassVar[tuple[Keys, ...]] = (
        Keys.KEY_LOWER_Q,
        Keys.KEY_UPPER_Q,
        Keys.KEY_CTRL_ESC,
    )
    _NAV_UP_KEYS: ClassVar[tuple[Keys, ...]] = (
        Keys.KEY_UP,
        Keys.KEY_LOWER_K,
        Keys.KEY_UPPER_K,
    )
    _NAV_DOWN_KEYS: ClassVar[tuple[Keys, ...]] = (
        Keys.KEY_DOWN,
        Keys.KEY_LOWER_J,
        Keys.KEY_UPPER_J,
    )
    _REFRESH_KEYS: ClassVar[tuple[Keys, ...]] = (
        Keys.KEY_LOWER_R,
        Keys.KEY_UPPER_R,
    )
    _ERASE_KEYS: ClassVar[tuple[Keys, ...]] = (Keys.KEY_BS, Keys.KEY_CTRL_BS)
    _DIGIT_KEYS: ClassVar[tuple[int, ...]] = tuple([ord(c) for c in digits])
    _SERIAL_KEYS: ClassVar[tuple[int, ...]] = tuple(
        [ord(c) for c in (ascii_letters + digits)]
    )

    def __init__(self, stdscr: curses.window) -> None:
        self.stdscr = stdscr
        curses.init_color(
            curses.COLOR_BLUE,
            self._ROYAL_BLUE_COLOR.r,
            self._ROYAL_BLUE_COLOR.g,
            self._ROYAL_BLUE_COLOR.b,
        )
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        self.stdscr.bkgd(" ", curses.color_pair(1))

    def _prepare_screen(self) -> tuple[int, int]:
        self.stdscr.erase()
        self.stdscr.border(
            curses.ACS_VLINE,
            curses.ACS_VLINE,
            curses.ACS_HLINE,
            curses.ACS_HLINE,
            curses.ACS_DIAMOND,
            curses.ACS_DIAMOND,
            curses.ACS_DIAMOND,
            curses.ACS_DIAMOND,
        )
        height, width = self.stdscr.getmaxyx()
        return height, width

    def show_loading(self, context: Sequence[str] | None = None) -> None:
        _, w = self._prepare_screen()
        self.stdscr.addstr(1, max(0, (w - len(TITLE)) // 2), TITLE)
        self.stdscr.addstr(2, max(0, (w - len(CREDITS)) // 2), CREDITS, curses.A_DIM)

        if context:
            for i, line in enumerate(context):
                self.stdscr.addstr(3 + i, 2, line, curses.A_DIM)

        y = 4 + (len(context) if context else 0) + 1
        self.stdscr.addstr(y, 2, "Carregando...", curses.A_BOLD)
        self.stdscr.refresh()

    def select_menu(
        self,
        question: str,
        options: Sequence[str],
        back: bool = False,
        context: Sequence[str] | None = None,
        can_exit: bool = True,
        default: int = 0,
        header: str | None = None,
        refresh: Callable[[], tuple[Sequence[str], str | None]] | None = None,
        no_result: Callable[[], None] | None = None,
        empty_message: str = "Nenhum resultado encontrado.",
    ) -> int | None:
        selected = max(0, min(default, len(options) - 1)) if options else 0
        top = 0

        while True:
            h, w = self._prepare_screen()

            hints: list[str] = []
            if options:
                hints.extend(
                    ["↑/↓, k/j, K/J ou 1-9 para navegar", "Enter para selecionar"]
                )
            if refresh is not None:
                hints.append("r/R para atualizar")
            if back:
                hints.append("q/Q/Esc para voltar")
            elif can_exit:
                hints.append("q/Q/Esc para sair")
            instructions = "(" + ", ".join(hints) + ")"

            self.stdscr.addstr(1, max(0, (w - len(TITLE)) // 2), TITLE)
            self.stdscr.addstr(
                2, max(0, (w - len(CREDITS)) // 2), CREDITS, curses.A_DIM
            )

            if context:
                for i, line in enumerate(context):
                    self.stdscr.addstr(3 + i, 2, line, curses.A_DIM)

            y_question = 4 + (len(context) if context else 0)
            self.stdscr.addstr(y_question, 2, question)
            self.stdscr.addstr(y_question + 1, 2, instructions)

            y_base = y_question + 3

            if not options:
                if no_result is not None:
                    no_result()
                else:
                    self.stdscr.addstr(y_base, 4, empty_message[: max(0, w - 6)])
            else:
                if header:
                    self.stdscr.addstr(y_base, 4, header, curses.A_BOLD)
                    self.stdscr.addstr(y_base + 1, 4, "-" * len(header), curses.A_DIM)
                    y_base += 2

                visible = max(1, h - y_base - 1)

                if selected < top:
                    top = selected
                elif selected >= top + visible:
                    top = selected - visible + 1

                for idx in range(top, min(top + visible, len(options))):
                    y = y_base + (idx - top)
                    attr = curses.A_REVERSE if idx == selected else curses.A_NORMAL
                    if header:
                        text = f"{options[idx]} "
                    else:
                        text = f"{idx + 1:03d} - {options[idx]} "
                    self.stdscr.addstr(y, 4, text, attr)

            self.stdscr.refresh()
            key = self.stdscr.getch()

            if key in self._CANCEL_KEYS:
                if back or can_exit:
                    return None
                continue
            elif refresh is not None and key in self._REFRESH_KEYS:
                refresh_context: list[str] = []
                if context:
                    refresh_context.extend(context)
                refresh_context.append("Atualizando...")
                self.show_loading(context=refresh_context)

                options, new_header = refresh()
                if new_header is not None:
                    header = new_header
                selected = max(0, min(selected, len(options) - 1)) if options else 0
                if not options:
                    top = 0
                continue
            elif not options:
                continue
            elif key in self._NAV_UP_KEYS:
                selected = (selected - 1) % len(options)
            elif key in self._NAV_DOWN_KEYS:
                selected = (selected + 1) % len(options)
            elif key in self._CONFIRM_KEYS:
                return selected
            elif key in self._DIGIT_KEYS[1::]:
                n = key - Keys.KEY_0
                if n <= min(len(options), 9):
                    return n - 1

    def show_result(
        self,
        title: str,
        lines: Sequence[str],
        context: Sequence[str] | None = None,
        refresh: Callable[[], Sequence[str]] | None = None,
    ) -> None:
        top = 0
        footer_hints = ["↑/↓, k/j ou K/J para rolar"]
        if refresh is not None:
            footer_hints.append("r/R para atualizar")
        footer_hints.append("q/Q/Esc para voltar")
        footer = "(" + ", ".join(footer_hints) + ")"

        while True:
            h, w = self._prepare_screen()

            self.stdscr.addstr(1, max(0, (w - len(TITLE)) // 2), TITLE)
            self.stdscr.addstr(
                2, max(0, (w - len(CREDITS)) // 2), CREDITS, curses.A_DIM
            )
            self.stdscr.addstr(4, 2, title[: max(0, w - 4)])

            clean_lines = [l.strip() for l in lines if l]
            y_base = 6
            visible = max(1, h - y_base - 3)
            max_top = max(0, len(clean_lines) - visible)
            top = min(top, max_top)

            for i in range(top, min(top + visible, len(clean_lines))):
                line_content = clean_lines[i][: max(0, w - 6)]
                self.stdscr.addstr(y_base + (i - top), 4, line_content)

            self.stdscr.addstr(h - 2, 2, footer[: max(0, w - 6)], curses.A_DIM)
            self.stdscr.refresh()

            key = self.stdscr.getch()
            if key in self._CANCEL_KEYS:
                return
            elif refresh is not None and key in self._REFRESH_KEYS:
                refresh_context: list[str] = []
                if context:
                    refresh_context.extend(context)
                else:
                    refresh_context.append(title)
                refresh_context.append("Atualizando...")
                self.show_loading(context=refresh_context)

                lines = refresh()
                top = 0
            elif key in self._NAV_UP_KEYS:
                top = max(0, top - 1)
            elif key in self._NAV_DOWN_KEYS:
                top = min(max_top, top + 1)

    def ask_input(
        self,
        question: str,
        context: Sequence[str] | None = None,
    ) -> str | None:
        buffer: list[str] = []
        instructions = "(Enter para confirmar, q/Q/Esc para cancelar)"

        while True:
            _, w = self._prepare_screen()

            self.stdscr.addstr(1, max(0, (w - len(TITLE)) // 2), TITLE)
            self.stdscr.addstr(
                2, max(0, (w - len(CREDITS)) // 2), CREDITS, curses.A_DIM
            )

            if context:
                for i, line in enumerate(context):
                    self.stdscr.addstr(3 + i, 2, line, curses.A_DIM)

            y_question = 4 + (len(context) if context else 0)
            self.stdscr.addstr(y_question, 2, question)

            y_input = y_question + 2
            self.stdscr.addstr(y_input, 2, "> " + "".join(buffer))
            self.stdscr.addstr(y_input + 1, 2, instructions, curses.A_DIM)
            self.stdscr.refresh()

            key = self.stdscr.getch()

            if key == Keys.KEY_CTRL_ESC:
                return None
            if key in self._CONFIRM_KEYS:
                return "".join(buffer)
            if key in self._ERASE_KEYS:
                if buffer:
                    buffer.pop()
                continue
            if (key == Keys.KEY_LOWER_Q or key == Keys.KEY_UPPER_Q) and not buffer:
                return None
            if key in self._SERIAL_KEYS:
                buffer.append(chr(key))
