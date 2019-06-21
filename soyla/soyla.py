# encoding: utf-8
import urwid

from .audio import AudioReadWriter, AudioDevice
from .model import SoylaModel
from .view import SoylaView
from .state import SoylaState


class Soyla(object):
    """
    Controller class for the program
    """
    def __init__(self, lines_file, save_dir, samplerate=44100):
        """
        :param lines_file: path to file containing lines
        :param save_dir: path to directory containing recorded wav files
        """
        self.save_dir = save_dir
        self.lines_file = lines_file

        self.audio = AudioDevice(samplerate)
        self.model = SoylaModel(self.lines_file, AudioReadWriter(self.save_dir, samplerate))
        self.view = SoylaView(self.model)

        self.set_state(SoylaState.WAITING)

    def update_lines_file(self):
        """
        rewrite file with updated lines
        """
        txt = '\n'.join(self.model.get_lines())
        with open(self.lines_file, 'w') as f:
            f.write(txt)

    def set_state(self, s):
        """
        update state
        :param s: SoylaState object
        """
        self.state = s
        self.view.update_state(s)

    def handle_input(self, key):
        """
        handles user keyboard input
        :param key: pressed key
        """
        def exit():
            raise urwid.ExitMainLoop()
        handlers = {
            SoylaState.WAITING: [
                (('q', 'Q'), exit),
                (('r', 'R'), self.record),
                ((' ',), self.play),
                (('j', 'J', 'down'), lambda: self.change_line(1)),
                (('k', 'K', 'up'), lambda: self.change_line(-1)),
                (('e', 'E'), self.edit),
            ],
            SoylaState.RECORDING: [
                (('r', 'R'), self.finish_record),
                (('esc',), self.cancel_record),
            ],
            SoylaState.PLAYING: [
                ((' ',), self.cancel_play),
            ],
            SoylaState.EDITING: [
                (('enter',), self.finish_edit),
                (('esc',), self.cancel_edit),
            ]
        }
        for ks, h in handlers[self.state]:
            if key in ks:
                return h()

    def cancel_record(self):
        """
        cancel recording audio
        """
        assert self.state == SoylaState.RECORDING
        self.audio.stop_recording()
        self.set_state(SoylaState.WAITING)

    def finish_record(self):
        """
        finish recording, save recorded audio
        """
        assert self.state == SoylaState.RECORDING
        data = self.audio.stop_recording()
        self.model.save_audio(self.model.l_index, data)
        self.view.update_sidebar_line(self.model.l_index)
        self.set_state(SoylaState.WAITING)
        self.view.update_line()
        self.view.show_saved()

    def record(self):
        """
        start recording audio
        """
        assert self.state == SoylaState.WAITING
        self.set_state(SoylaState.RECORDING)
        self.audio.start_recording()

    def cancel_play(self):
        """
        stop audio playback
        """
        assert self.state == SoylaState.PLAYING
        self.audio.stop_playing()

    def play(self):
        """
        start audio playback if current line has one
        """
        assert self.state == SoylaState.WAITING
        if self.model.cur_audio() is None:
            return
        self.set_state(SoylaState.PLAYING)

        def fcallback():
            self.set_state(SoylaState.WAITING)
            self.force_draw()
        self.audio.play(self.model.cur_audio(), cb=fcallback)

    def change_line(self, d):
        """
        change selected line
        """
        assert self.state == SoylaState.WAITING
        self.model.change_line(d)
        self.view.update_line()

    def edit(self):
        """
        start editing of selected line
        """
        assert self.state == SoylaState.WAITING
        self.view.start_edit()
        self.set_state(SoylaState.EDITING)

    def cancel_edit(self):
        """
        cancel editing
        """
        assert self.state == SoylaState.EDITING
        self.view.finish_edit()
        self.set_state(SoylaState.WAITING)

    def finish_edit(self):
        """
        finish editing, save text of edited line
        """
        assert self.state == SoylaState.EDITING
        edit_txt = self.view.finish_edit()
        self.model.update_line(self.model.l_index, edit_txt)
        self.view.update_sidebar_line(self.model.l_index)
        self.update_lines_file()
        self.set_state(SoylaState.WAITING)
        self.view.update_line()
        self.view.show_saved()

    def force_draw(self):
        """
        force drawing screen
        """
        self.loop.draw_screen()

    def run(self):
        """
        run the program
        """
        self.loop = urwid.MainLoop(
            self.view.top_widget(),
            unhandled_input=lambda k: self.handle_input(k),
            palette=self.view.PALETTE,
        )
        self.loop.run()
