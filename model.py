# encoding: utf-8


class SoylaModel(object):
    """
    Class handles loading/saving text lines as
    well as wav files io. Also keeps track of
    currently selected line.
    """
    def __init__(self, lines_file, audiorw):
        """
        :param lines_file: path to file with lines
        :param audiorw: AudioReadWriter instance
        """
        self.lines_file = lines_file
        self.audiorw = audiorw
        self._read_lines()

    def _read_lines(self):
        """
        reads lines from file and sets index
        for selected line
        """
        with open(self.lines_file, 'r') as f:
            txt_lines = f.readlines()
        self.lines = [l.strip() for l in txt_lines]
        self.lines_len = len(self.lines)
        self._l_index = 0
        # set first line that does not have recorded audio
        # as selected
        for i in range(self.lines_len):
            if i not in self.audiorw:
                self._l_index = i
                break

    def change_line(self, d):
        """
        change currently selected line
        :param d: delta (for example, 1: next line, -1: previous line)
        """
        self._l_index = self._l_index + d
        if self._l_index < 0:
            self._l_index = 0
        elif self._l_index >= self.lines_len:
            self._l_index = self.lines_len - 1

    def get_lines(self):
        """
        :returns: all lines in the project
        """
        return self.lines

    def line_has_audio(self, i):
        """
        :param i: index of line
        :returns: bool, whether the line has recorded audio
        """
        return i in self.audiorw

    def get_current_line(self):
        """
        :returns: text of currently selected line
        """
        return self.lines[self._l_index]

    def cur_audio_length(self):
        """
        :returns: audio length of currently selected line
        """
        return self.audiorw.length(self._l_index)

    def audio_sum_length(self):
        """
        :returns: sum of all recorded audio lengths in seconds
        """
        return self.audiorw.sum_length

    def cur_audio(self):
        """
        :returns: audio data of currently selected line
        """
        return self.audiorw.data(self._l_index)

    def save_audio(self, i, data):
        """
        saves audio to wav file
        :param i: index of line
        :param data: numpy array of audio data
        """
        self.audiorw[i] = data

    def update_line(self, i, txt):
        """
        updates line text
        :param i: index of line
        :param txt: new text
        """
        self.lines[i] = txt

    @property
    def l_index(self):
        """
        index of currently selected line
        """
        return self._l_index
