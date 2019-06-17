# encoding: utf-8
import numpy as np
import glob
import os
import sounddevice as sd
from scipy.io import wavfile


class AudioReadWriter(object):
    def __init__(self, wav_dir, samplerate):
        self.wav_dir = wav_dir
        self.samplerate = samplerate
        self._read_audio_lengths()

    def _calc_sum_len(self):
        self.sum_length = 0
        for v in self._lengths.values():
            self.sum_length += v

    def _read_audio_lengths(self):
        wavs = glob.glob(os.path.join(self.wav_dir, '*.wav'))
        self._lengths = {}
        for w in wavs:
            i = os.path.splitext(os.path.basename(w))[0]
            try:
                i = int(i)
            except ValueError:
                continue
            _, s = wavfile.read(w)
            self._lengths[i] = s.shape[0] / self.samplerate
        self._calc_sum_len()

    def data(self, i):
        if i not in self._lengths:
            return None
        _, s = wavfile.read(os.path.join(self.wav_dir, "{}.wav".format(i)))
        return s

    def length(self, i):
        return self._lengths.get(i)

    def save(self, i, data):
        wavfile.write(os.path.join(self.wav_dir, '{}.wav'.format(i)),
                      self.samplerate, data)
        self._lengths[i] = data.shape[0] / self.samplerate
        self._calc_sum_len()

    def __setitem__(self, key, value):
        if type(key) != int:
            raise TypeError("key must be int")
        self.save(key, value)

    def __contains__(self, i):
        return i in self._lengths


class AudioDevice(object):
    def __init__(self, samplerate):
        self.samplerate = samplerate

    def play(self, data, cb=None):
        def callback(outdata, frames, time, status):
            if self._play_frames + frames > self._play_buf.size:
                raise sd.CallbackStop()
            outdata[:, 0] = self._play_buf[self._play_frames:self._play_frames + frames]
            self._play_frames += frames

        self._play_buf = np.copy(data)
        self._play_frames = 0
        self._out_stream = sd.OutputStream(channels=1, samplerate=self.samplerate,
                                           callback=callback, finished_callback=cb)
        self._out_stream.start()

    def stop_playing(self):
        self._out_stream.stop()

    def start_recording(self):
        self._indata = []

        def callback(indata, frames, time, status):
            self._indata.append(np.copy(indata[:, 0]))
        self._in_stream = sd.InputStream(channels=1, samplerate=self.samplerate, callback=callback)
        self._in_stream.start()

    def stop_recording(self):
        self._in_stream.stop()
        self._in_stream.close()
        return np.concatenate(self._indata)
