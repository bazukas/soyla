# encoding: utf-8
import numpy as np
import sounddevice as sd
import threading
import urwid
import os
from scipy.io import wavfile


class MyEdit(urwid.Edit):
    def keypress(self, size, key):
        if key == 'enter':
            return 'enter'
        super(MyEdit, self).keypress(size, key)


class MyListBox(urwid.ListBox):
    def keypress(self, size, key):
        return key


class Soyla(object):
    WAITING = 0
    RECORDING = 1
    PLAYING = 2
    EDITING = 3

    SAMPLERATE = 44100

    PALETTE = [
        ('reversed', 'standout', ''),
    ]

    def __init__(self, lines_file, save_dir):
        self.save_dir = save_dir
        self.lines_file = lines_file
        self._init_state()
        self._init_widgets()
        self.draw()

    def _read_lines(self):
        with open(self.lines_file, 'r') as f:
            txt_lines = f.readlines()
        self.lines = [(l.strip(), None, False) for l in txt_lines]
        self.lines_len = len(self.lines)
        self.l_index = 0

    def _save_lines(self):
        txt = '\n'.join([l[0] for l in self.lines])
        with open(self.lines_file, 'w') as f:
            f.write(txt)

    def _init_state(self):
        self._read_lines()
        self.state = self.WAITING

    def _init_widgets(self):
        self.state_text = urwid.Text('', align='center')
        self.line_text = urwid.Text('', align='center')
        self.line_edit = urwid.Edit(align='center')
        self.line = urwid.WidgetPlaceholder(self.line_text)
        self.line_list = MyListBox(urwid.SimpleFocusListWalker(self._get_side_list()))
        main_window = urwid.Pile([
            ('weight', 1, urwid.Filler(self.line)),
            ('pack', urwid.Divider('-')),
            ('weight', 1, urwid.Filler(self.state_text)),
        ])
        self.top = urwid.Columns([
            ('weight', 1, self.line_list),
            ('weight', 2, main_window),
        ], dividechars=3)

    def _get_side_list(self):
        lines = [l[0] for l in self.lines]
        for i, l in enumerate(lines):
            lines[i] = "{}. {}".format(i, l)
        # lines = [l + '...' for l in lines]
        lines = [urwid.Text(l, wrap='clip') for l in lines]
        lines = [urwid.AttrMap(l, None, focus_map='reversed') for l in lines]
        return lines

    def handle_input(self, key):
        if key in ('q', 'Q', 'esc'):
            if self.state == self.EDITING:
                return self.cancel_edit()
            raise urwid.ExitMainLoop()
        if key in ('r', 'R'):
            return self.record()
        if key in ('s', 'S'):
            return self.save()
        if key == ' ':
            return self.play()
        if key in ('j', 'J', 'down'):
            return self.change_line(1)
        if key in ('k', 'K', 'up'):
            return self.change_line(-1)
        if key in ('e', 'E'):
            return self.edit()
        if key == 'enter':
            return self.finish_edit()

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
        self.line_list.set_focus(self.l_index)
        self.draw()

    def edit(self):
        if self.state != self.WAITING:
            return
        self.line.original_widget = self.line_edit
        self.line_edit.set_edit_text(self.cur_line)
        self.line_edit.set_edit_pos(len(self.cur_line))
        self.top.set_focus(1)
        self.set_state(self.EDITING)

    def cancel_edit(self):
        if self.state != self.EDITING:
            return
        self.line.original_widget = self.line_text
        self.top.set_focus(0)
        self.set_state(self.WAITING)

    def finish_edit(self):
        if self.state != self.EDITING:
            return
        self.line.original_widget = self.line_text
        self.cur_line = self.line_edit.get_edit_text()
        self._save_lines()
        self.top.set_focus(0)
        self.set_state(self.WAITING)

    def run(self):
        self.loop = urwid.MainLoop(
            self.top,
            unhandled_input=lambda k: self.handle_input(k),
            pop_ups=True,
            palette=self.PALETTE,
        )
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
        elif self.state == self.EDITING:
            txt = "Editing text"
        else:
            txt = "Waiting"
        self.state_text.set_text(txt)

    @property
    def cur_line(self):
        return self.lines[self.l_index][0]

    @cur_line.setter
    def cur_line(self, l):
        _, s, b = self.lines[self.l_index]
        self.lines[self.l_index] = (l, s, b)

    @property
    def cur_sound(self):
        return self.lines[self.l_index][1]

    @cur_sound.setter
    def cur_sound(self, s):
        self.lines[self.l_index] = (self.cur_line, s, True)

    def _draw_line_text(self):
        self.line_text.set_text(self.cur_line)


def main(input_file, save_dir):
    s = Soyla(input_file, save_dir)
    s.run()
