# encoding: utf-8
import glob
import numpy as np
import sounddevice as sd
import urwid
import os
from scipy.io import wavfile


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
        ('screen edge', 'black', 'black'),
        ('line', 'light gray', 'black'),
        ('main', 'light gray', 'black'),
        ('reversed', 'standout', ''),
        ('check', 'dark green', 'black'),
        ('text', 'white,bold', 'black'),
        ('state', 'dark green', 'black'),
        ('recording', 'light red', 'black'),
        ('instructions', 'light magenta', 'black'),
        ('status', 'yellow', 'black'),
    ]

    def __init__(self, lines_file, save_dir):
        self.save_dir = save_dir
        self.lines_file = lines_file
        self._init_state()
        self._init_widgets()
        self._calculate_total_audio_length()
        self.draw()

    def _read_wavs(self):
        wavs = glob.glob(os.path.join(self.save_dir, '*.wav'))
        res = {}
        for w in wavs:
            i = os.path.splitext(os.path.basename(w))[0]
            try:
                i = int(i)
            except ValueError:
                continue
            _, res[i] = wavfile.read(w)
        return res

    def _read_lines(self):
        with open(self.lines_file, 'r') as f:
            txt_lines = f.readlines()
        wavs = self._read_wavs()
        self.lines = [(l.strip(), wavs.get(i), False) for i, l in enumerate(txt_lines)]
        self.lines_len = len(self.lines)
        self.l_index = 0
        for i in range(self.lines_len):
            if i not in wavs:
                self.l_index = i
                break

    def _save_lines(self):
        txt = '\n'.join([l[0] for l in self.lines])
        with open(self.lines_file, 'w') as f:
            f.write(txt)

    def _init_state(self):
        self._read_lines()
        self.state = self.WAITING

    def _init_widgets(self):
        self.instructions_text = urwid.Text('', align='left')
        self.state_text = urwid.Text('', align='center')
        self.line_text = urwid.Text('', align='center')
        self.line_edit = urwid.Edit(align='center')
        self.line = urwid.WidgetPlaceholder(self.line_text)
        self.line_list = self._get_side_list()
        self.line_listbox = MyListBox(urwid.SimpleFocusListWalker(self.line_list))
        self.line_listbox.set_focus(self.l_index)
        self.total_audio_text = urwid.Text('')
        self.audio_status_line = urwid.Text('', align='center')
        self.status_line = urwid.Text('', align='right')
        vline = urwid.AttrMap(urwid.SolidFill(u'\u2502'), 'line')
        hline = urwid.AttrMap(urwid.Divider('─'), 'line')
        status = urwid.Columns([
            ('weight', 1, self.total_audio_text),
            ('weight', 1, self.audio_status_line),
            ('weight', 1, self.status_line),
        ])
        status = urwid.AttrMap(status, 'status')
        state_instr = urwid.Columns([
            ('weight', 1, urwid.Filler(self.state_text)),
            ('fixed', 1, vline),
            ('weight', 1, urwid.Filler(urwid.Padding(self.instructions_text, 'center', width='pack'))),
        ])
        main_window = urwid.Pile([
            ('weight', 1, urwid.AttrMap(urwid.Filler(self.line), 'text')),
            ('pack', hline),
            ('weight', 1, state_instr),
            ('pack', hline),
            (1, urwid.Padding(urwid.Filler(status), left=1, right=1)),
        ])
        self.top = urwid.Columns([
            ('weight', 1, urwid.Padding(self.line_listbox, left=1, right=1)),
            ('fixed', 1, vline),
            ('weight', 2, main_window),
        ])
        bg = urwid.AttrMap(urwid.SolidFill(u"\u2592"), 'screen edge')
        w = urwid.LineBox(urwid.AttrMap(self.top, 'main'))
        w = urwid.AttrMap(w, 'line')
        self.overlay = urwid.Overlay(w, bg,
                                     ('fixed left', 1), ('fixed right', 1),
                                     ('fixed top', 0), ('fixed bottom', 0))

    def _calculate_total_audio_length(self):
        al = 0
        for l in self.lines:
            if l[1] is not None:
                al += float(l[1].size / self.SAMPLERATE)
        self.total_audio_length = al

    def _format_line_for_sidebar(self, i):
        check = '  ' if self.lines[i][1] is None else u'\u2714 '
        return [('check', check), " {}. {}".format(i, self.lines[i][0])]

    def _get_side_list(self):
        lines = [l[0] for l in self.lines]
        lines = []
        for i, l in enumerate(self.lines):
            lines.append(self._format_line_for_sidebar(i))
        lines = [urwid.Text(l, wrap='clip') for l in lines]
        lines = [urwid.AttrMap(l, None, focus_map='reversed') for l in lines]
        return lines

    def handle_input(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        if key == 'esc':
            if self.state == self.EDITING:
                return self.cancel_edit()
            elif self.state == self.RECORDING:
                return self.cancel_record()
        if key in ('r', 'R'):
            return self.record()
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

    def cancel_record(self):
        if self.state != self.RECORDING:
            return
        self.stream.stop()
        self.stream.close()
        self.set_state(self.WAITING)

    def record(self):
        if self.state == self.RECORDING:
            self.stream.stop()
            self.stream.close()
            self.cur_sound = np.concatenate(self.indata)
            self.save_current()
            self.set_state(self.WAITING)
            self.status_line.set_text("Saved")
        elif self.state == self.WAITING:
            self.set_state(self.RECORDING)
            self.indata = []

            def callback(indata, frames, time, status):
                self.indata.append(np.copy(indata[:, 0]))
            self.stream = sd.InputStream(channels=1, samplerate=self.SAMPLERATE, callback=callback)
            self.stream.start()

    def play(self):
        if self.state == self.PLAYING:
            self.out_stream.stop()
            return
        if self.state != self.WAITING or self.cur_sound is None:
            return
        self.set_state(self.PLAYING)

        def fcallback():
            self.set_state(self.WAITING)
            self.force_paint()

        def callback(outdata, frames, time, status):
            if self.play_frames + frames > self.play_buf.size:
                raise sd.CallbackStop()
            outdata[:, 0] = self.play_buf[self.play_frames:self.play_frames + frames]
            self.play_frames += frames

        self.play_buf = np.copy(self.cur_sound)
        self.play_frames = 0
        self.out_stream = sd.OutputStream(channels=1, samplerate=self.SAMPLERATE,
                                          callback=callback, finished_callback=fcallback)
        self.out_stream.start()

    def save_current(self):
        wavfile.write(os.path.join(self.save_dir, '%d.wav') % self.l_index,
                      self.SAMPLERATE, self.cur_sound)
        self.line_list[self.l_index].original_widget.set_text(self._format_line_for_sidebar(self.l_index))
        self._calculate_total_audio_length()

    def change_line(self, d):
        if self.state != self.WAITING:
            return
        self.l_index = self.l_index + d
        if self.l_index < 0:
            self.l_index = 0
        elif self.l_index >= self.lines_len:
            self.l_index = self.lines_len - 1
        self.line_listbox.set_focus(self.l_index)
        self.draw()

    def edit(self):
        if self.state != self.WAITING:
            return
        self.line.original_widget = self.line_edit
        self.line_edit.set_edit_text(self.cur_line)
        self.line_edit.set_edit_pos(len(self.cur_line))
        self.top.set_focus(2)
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
        self.line_list[self.l_index].original_widget.set_text(self._format_line_for_sidebar(self.l_index))
        self.set_state(self.WAITING)
        self.status_line.set_text("Saved")

    def run(self):
        self.loop = urwid.MainLoop(
            self.overlay,
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
        self._draw_audio_status_line()
        self.status_line.set_text("")
        self.total_audio_text.set_text("Project audio length: {:.2f} seconds".format(self.total_audio_length))
        self._draw_instructions()

    def _draw_instructions(self):
        instr = ''
        if self.state == self.WAITING:
            instr = ("Q - exit program\n"
                     "J - next line\n"
                     "K - previous line\n"
                     "R - record line\n"
                     "E - edit text\n"
                     "<space> - play"
                     )
        elif self.state == self.RECORDING:
            instr = ("R - finish recording\n"
                     "<esc> - cancel recording"
                     )
        elif self.state == self.PLAYING:
            instr = "<space> - stop plaing"
        elif self.state == self.EDITING:
            instr = ("<enter> - save line\n"
                     "<esc> - cancel editing"
                     )

        self.instructions_text.set_text(('instructions', instr))

    def _draw_state_text(self):
        if self.state == self.RECORDING:
            txt = ('recording', "Recording")
        elif self.state == self.PLAYING:
            txt = ('state', "Playing")
        elif self.state == self.EDITING:
            txt = ('state', "Editing text")
        else:
            txt = ('state', "Waiting")
        self.state_text.set_text(txt)

    def _draw_audio_status_line(self):
        status = ""
        if self.cur_sound is None:
            status = "No recording"
        else:
            length = self.cur_sound.size / self.SAMPLERATE
            status = "Recording length: {:.2f} seconds".format(length)
        self.audio_status_line.set_text(status)

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
