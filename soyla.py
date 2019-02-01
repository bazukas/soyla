# encoding: utf-8
import numpy as np
import sounddevice as sd
import threading
import urwid
from scipy.io import wavfile


class Soyla(object):
    WAITING = 0
    RECORDING = 1
    PLAYING = 2

    SAMPLERATE = 44100

    def __init__(self):
        self.txt = urwid.Text("")
        self.fill = urwid.Filler(self.txt, "top")
        self.sound = None
        self.state = self.WAITING
        self.draw()

    def handle_input(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        if key in ('r', 'R'):
            return self.record()
        if key in ('s', 'S'):
            return self.save()
        if key == ' ':
            return self.play()

    def set_state(self, s):
        self.state = s
        self.draw()

    def record(self):
        if self.state == self.RECORDING:
            self.stream.stop()
            self.stream.close()
            self.sound = np.concatenate(self.indata)
            self.set_state(self.WAITING)
        elif self.state == self.WAITING:
            self.set_state(self.RECORDING)
            self.indata = []

            def callback(indata, frames, time, status):
                self.indata.append(np.copy(indata))
            self.stream = sd.InputStream(channels=1, samplerate=self.SAMPLERATE, callback=callback)
            self.stream.start()

    def play(self):
        if self.state != self.WAITING or self.sound is None:
            return
        self.set_state(self.PLAYING)

        def task():
            sd.play(self.sound, samplerate=self.SAMPLERATE)
            sd.wait()
            self.set_state(self.WAITING)
            self.force_paint()
        threading.Thread(target=task).start()

    def save(self):
        if self.sound is None:
            return
        wavfile.write('test.wav', self.SAMPLERATE, self.sound)

    def draw(self):
        if self.state == self.RECORDING:
            self.txt.set_text("Recording")
        elif self.state == self.PLAYING:
            self.txt.set_text("Playing")
        else:
            self.txt.set_text("Waiting")

    def force_paint(self):
        self.loop.draw_screen()

    def run(self):
        self.loop = urwid.MainLoop(self.fill, unhandled_input=lambda k: self.handle_input(k))
        self.loop.run()


def main():
    s = Soyla()
    s.run()
