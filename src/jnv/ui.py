import curses
from collections.abc import Sequence

from .constants import CREDITS, TITLE


class UI:
    def __init__(self, stdscr: curses.window) -> None:
        self.stdscr = stdscr

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
    ) -> int | None:
        selected = max(0, min(default, len(options) - 1))
        top = 0
        hints = ["↑/↓ navegar", "Enter selecionar"]

        if back:
            hints.append("q voltar")
        elif can_exit:
            hints.append("q sair")
        instructions = "(" + ", ".join(hints) + ")"

        while True:
            h, w = self._prepare_screen()

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
            visible = max(1, h - y_base - 1)

            if selected < top:
                top = selected
            elif selected >= top + visible:
                top = selected - visible + 1

            for idx in range(top, min(top + visible, len(options))):
                y = y_base + (idx - top)
                attr = curses.A_REVERSE if idx == selected else curses.A_NORMAL
                self.stdscr.addstr(y, 4, f"{idx + 1:03d} - {options[idx]} ", attr)

            self.stdscr.refresh()
            key = self.stdscr.getch()

            if key in (ord("q"), ord("Q"), 27):
                if back or can_exit:
                    return None
                continue
            elif key in (curses.KEY_UP, ord("k")):
                selected = (selected - 1) % len(options)
            elif key in (curses.KEY_DOWN, ord("j")):
                selected = (selected + 1) % len(options)
            elif key in (10, 13, curses.KEY_ENTER):
                return selected
            elif ord("1") <= key <= ord("9"):
                n = key - ord("0")
                if n <= min(len(options), 9):
                    return n - 1

    def show_result(self, title: str, lines: Sequence[str]) -> None:
        top = 0
        while True:
            h, w = self._prepare_screen()

            self.stdscr.addstr(1, max(0, (w - len(TITLE)) // 2), TITLE)
            self.stdscr.addstr(
                2, max(0, (w - len(CREDITS)) // 2), CREDITS, curses.A_DIM
            )
            self.stdscr.addstr(4, 2, title[: max(0, w - 4)])

            y_base = 6
            visible = max(1, h - y_base - 3)
            max_top = max(0, len(lines) - visible)
            top = min(top, max_top)

            lines = [l.strip() for l in lines if l]

            for i in range(top, min(top + visible, len(lines))):
                line_content = lines[i][: max(0, w - 6)]
                self.stdscr.addstr(y_base + (i - top), 4, line_content)

            footer = "(↑/↓ rolar, qualquer outra tecla volta)"
            self.stdscr.addstr(h - 2, 2, footer[: max(0, w - 6)], curses.A_DIM)
            self.stdscr.refresh()

            key = self.stdscr.getch()
            if key in (curses.KEY_UP, ord("k")):
                top = max(0, top - 1)
            elif key in (curses.KEY_DOWN, ord("j")):
                top = min(max_top, top + 1)
            else:
                return
