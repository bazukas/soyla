# encoding: utf-8
import numpy as np
import sounddevice as sd
import threading
import urwid
import os
from scipy.io import wavfile


class Soyla(object):
    WAITING = 0
    RECORDING = 1
    PLAYING = 2

    SAMPLERATE = 44100

    def __init__(self, lines, save_dir):
        self.save_dir = save_dir
        self._init_state(lines)
        self._init_widgets()
        self.draw()

    def _init_state(self, txt_lines):
        self.state = self.WAITING
        self.lines = [(l, None, False) for l in txt_lines]
        self.lines_len = len(self.lines)
        self.l_index = 0

    def _init_widgets(self):
        self.state_text = urwid.Text('', align='center')
        self.line_text = urwid.Text('', align='center')
        pile = urwid.Pile([
            ('weight', 1, urwid.Filler(self.line_text)),
            ('pack', urwid.Divider('-')),
            ('weight', 1, urwid.Filler(self.state_text)),
        ])
        self.top = pile

    def handle_input(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        if key in ('r', 'R'):
            return self.record()
        if key in ('s', 'S'):
            return self.save()
        if key == ' ':
            return self.play()
        if key in ('j', 'J'):
            return self.change_line(1)
        if key in ('k', 'K'):
            return self.change_line(-1)

    def set_state(self, s):
        self.state = s
        self.draw()

    def record(self):
        if self.state == self.RECORDING:
            self.stream.stop()
            self.stream.close()
            self.cur_sound = np.concatenate(self.indata)
            self.set_state(self.WAITING)
        elif self.state == self.WAITING:
            self.set_state(self.RECORDING)
            self.indata = []

            def callback(indata, frames, time, status):
                self.indata.append(np.copy(indata))
            self.stream = sd.InputStream(channels=1, samplerate=self.SAMPLERATE, callback=callback)
            self.stream.start()

    def play(self):
        if self.state != self.WAITING or self.cur_sound is None:
            return
        self.set_state(self.PLAYING)

        def task():
            sd.play(self.cur_sound, samplerate=self.SAMPLERATE)
            sd.wait()
            self.set_state(self.WAITING)
            self.force_paint()
        threading.Thread(target=task).start()

    def save(self):
        if self.state != self.WAITING:
            return
        for i, l in enumerate(self.lines):
            if l[2] and l[1] is not None:
                wavfile.write(os.path.join(self.save_dir, '%d.wav') % i, self.SAMPLERATE, l[1])

    def change_line(self, d):
        if self.state != self.WAITING:
            return
        self.l_index = self.l_index + d
        if self.l_index < 0:
            self.l_index = 0
        elif self.l_index >= self.lines_len:
            self.l_index = self.lines_len - 1
        self.draw()

    def run(self):
        self.loop = urwid.MainLoop(self.top, unhandled_input=lambda k: self.handle_input(k))
        self.loop.run()

    def force_paint(self):
        self.loop.draw_screen()

    def draw(self):
        self._draw_state_text()
        self._draw_line_text()

    def _draw_state_text(self):
        if self.state == self.RECORDING:
            txt = "Recording"
        elif self.state == self.PLAYING:
            txt = "Playing"
        else:
            txt = "Waiting"
        self.state_text.set_text(txt)

    @property
    def cur_line(self):
        return self.lines[self.l_index][0]

    @property
    def cur_sound(self):
        return self.lines[self.l_index][1]

    @cur_sound.setter
    def cur_sound(self, s):
        self.lines[self.l_index] = (self.cur_line, s, True)

    def _draw_line_text(self):
        txt = "%d. %s" % (self.l_index, self.cur_line)
        self.line_text.set_text(txt)


def read_lines(input_file):
    with open(input_file, 'r') as f:
        lines = f.readlines()
    return lines


def main(input_file, save_dir):
    lines = read_lines(input_file)
    s = Soyla(lines, save_dir)
    s.run()
