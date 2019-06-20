# encoding: utf-8
from enum import Enum, unique


_TXTS = {
    0: "Waiting",
    1: "Recording",
    2: "Playing",
    3: "Editing text",
}

_INSTRS = {
    0: ("Q - exit program\n"
        "J - next line\n"
        "K - previous line\n"
        "R - record line\n"
        "E - edit text\n"
        "<space> - play"
        ),
    1: ("R - finish recording\n"
        "<esc> - cancel recording"
        ),
    2: "<space> - stop plaing",
    3: ("<enter> - save line\n"
        "<esc> - cancel editing"
        ),
}


@unique
class SoylaState(Enum):
    """
    Enum for possible states of program
    """
    WAITING = 0
    RECORDING = 1
    PLAYING = 2
    EDITING = 3

    def text(self):
        return _TXTS[self.value]

    def instruction(self):
        return _INSTRS[self.value]
