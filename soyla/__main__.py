# encoding: utf-8
import argparse
from pathlib import Path

from .soyla import Soyla


def main(input_file, save_dir, samplerate=44100):
    s = Soyla(input_file, save_dir, samplerate=samplerate)
    s.run()


parser = argparse.ArgumentParser("soyla")
parser.add_argument('lines', type=Path, help='path to file with lines')
parser.add_argument('wav_dir', type=Path, help='path to directory containing wav files')
parser.add_argument('-sr', '--samplerate', type=int, default=44100, help='audio samplerate, default: 44100')

if __name__ == '__main__':
    args = parser.parse_args()
    main(args.lines, args.wav_dir, args.samplerate)
