import curses
from enum import IntEnum


class Keys(IntEnum):
    KEY_CTRL_BACKSPACE = ord("\b")
    KEY_CTRL_CR = ord("\r")
    KEY_CTRL_ESC = ord("\x1b")
    KEY_CTRL_LF = ord("\n")

    KEY_BACKSPACE = curses.KEY_BACKSPACE
    KEY_ENTER = curses.KEY_ENTER
    KEY_DOWN = curses.KEY_DOWN
    KEY_UP = curses.KEY_UP

    KEY_LOWER_J = ord("j")
    KEY_UPPER_J = ord("J")
    KEY_LOWER_K = ord("k")
    KEY_UPPER_K = ord("K")
    KEY_LOWER_Q = ord("q")
    KEY_UPPER_Q = ord("Q")

    KEY_0 = ord("0")
