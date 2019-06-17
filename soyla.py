# encoding: utf-8
import urwid

from audio import AudioReadWriter, AudioDevice
from model import SoylaModel
from view import SoylaView
from state import SoylaState


class Soyla(object):
    SAMPLERATE = 44100

    def __init__(self, lines_file, save_dir):
        self.save_dir = save_dir
        self.lines_file = lines_file

        self.audio = AudioDevice(self.SAMPLERATE)
        self.model = SoylaModel(self.lines_file, AudioReadWriter(self.save_dir, self.SAMPLERATE))
        self.view = SoylaView(self.model)

        self.set_state(SoylaState.WAITING)

    def update_lines_file(self):
        txt = '\n'.join(self.model.get_lines())
        with open(self.lines_file, 'w') as f:
            f.write(txt)

    def handle_input(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        if key == 'esc':
            if self.state == SoylaState.EDITING:
                return self.cancel_edit()
            elif self.state == SoylaState.RECORDING:
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
        self.view.update_state(s)

    def cancel_record(self):
        if self.state != SoylaState.RECORDING:
            return
        self.audio.stop_recording()
        self.set_state(SoylaState.WAITING)

    def record(self):
        if self.state == SoylaState.RECORDING:
            data = self.audio.stop_recording()
            self.model.save_audio(self.model.l_index, data)
            self.view.update_sidebar_line(self.model.l_index)
            self.set_state(SoylaState.WAITING)
            self.view.update_line()
            self.view.show_saved()
        elif self.state == SoylaState.WAITING:
            self.set_state(SoylaState.RECORDING)
            self.audio.start_recording()

    def play(self):
        if self.state == SoylaState.PLAYING:
            self.audio.stop_playing()
            return
        if self.state != SoylaState.WAITING or self.model.cur_audio() is None:
            return
        self.set_state(SoylaState.PLAYING)

        def fcallback():
            self.set_state(SoylaState.WAITING)
            self.force_paint()
        self.audio.play(self.model.cur_audio(), cb=fcallback)

    def change_line(self, d):
        if self.state != SoylaState.WAITING:
            return
        self.model.change_line(d)
        self.view.update_line()

    def edit(self):
        if self.state != SoylaState.WAITING:
            return
        self.view.start_edit()
        self.set_state(SoylaState.EDITING)

    def cancel_edit(self):
        if self.state != SoylaState.EDITING:
            return
        self.view.finish_edit()
        self.set_state(SoylaState.WAITING)

    def finish_edit(self):
        if self.state != SoylaState.EDITING:
            return
        edit_txt = self.view.finish_edit()
        self.model.update_line(self.model.l_index, edit_txt)
        self.view.update_sidebar_line(self.model.l_index)
        self.update_lines_file()
        self.set_state(SoylaState.WAITING)
        self.view.update_line()
        self.view.show_saved()

    def run(self):
        self.loop = urwid.MainLoop(
            self.view.top_widget(),
            unhandled_input=lambda k: self.handle_input(k),
            palette=self.view.PALETTE,
        )
        self.loop.run()

    def force_paint(self):
        self.loop.draw_screen()


def main(input_file, save_dir):
    s = Soyla(input_file, save_dir)
    s.run()
