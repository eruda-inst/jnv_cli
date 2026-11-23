import curses
import curses.ascii
from enum import IntEnum


class Keys(IntEnum):
    KEY_CTRL_BS = curses.ascii.BS
    KEY_CTRL_CR = curses.ascii.CR
    KEY_CTRL_ESC = curses.ascii.ESC
    KEY_CTRL_LF = curses.ascii.LF

    KEY_BS = curses.KEY_BACKSPACE
    KEY_ENTER = curses.KEY_ENTER
    KEY_DOWN = curses.KEY_DOWN
    KEY_UP = curses.KEY_UP

    KEY_LOWER_J = ord("j")
    KEY_UPPER_J = ord("J")
    KEY_LOWER_K = ord("k")
    KEY_UPPER_K = ord("K")
    KEY_LOWER_Q = ord("q")
    KEY_UPPER_Q = ord("Q")
    KEY_LOWER_R = ord("r")
    KEY_UPPER_R = ord("R")

    KEY_0 = ord("0")
