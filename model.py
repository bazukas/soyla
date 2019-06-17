# encoding: utf-8


class SoylaModel(object):
    def __init__(self, lines_file, audiorw):
        self.lines_file = lines_file
        self.audiorw = audiorw
        self._read_lines()

    def _read_lines(self):
        with open(self.lines_file, 'r') as f:
            txt_lines = f.readlines()
        self.lines = [l.strip() for l in txt_lines]
        self.lines_len = len(self.lines)
        self._l_index = 0
        for i in range(self.lines_len):
            if i not in self.audiorw:
                self._l_index = i
                break

    def change_line(self, d):
        self._l_index = self._l_index + d
        if self._l_index < 0:
            self._l_index = 0
        elif self._l_index >= self.lines_len:
            self._l_index = self.lines_len - 1

    def get_lines(self):
        return self.lines

    def line_has_audio(self, i):
        return i in self.audiorw

    def get_current_line(self):
        return self.lines[self._l_index]

    def cur_audio_length(self):
        return self.audiorw.length(self._l_index)

    def audio_sum_length(self):
        return self.audiorw.sum_length

    def cur_audio(self):
        return self.audiorw.data(self._l_index)

    def save_audio(self, i, data):
        self.audiorw[i] = data

    def update_line(self, i, txt):
        self.lines[i] = txt

    @property
    def l_index(self):
        return self._l_index
