"""A tiny synthesiser: renders notes to a WAV file and plays it, using only the standard library."""
import atexit
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import wave
from array import array
from functools import lru_cache

RATE = 22050
# (harmonic, loudness) pairs give a soft, piano-like tone
HARMONICS = [(1, 1.0), (2, 0.45), (3, 0.2), (4, 0.1)]
FADE = 0.03  # seconds of fade-out at the end of each note, so it doesn't click


def frequency(midi):
    return 440 * 2 ** ((midi - 69) / 12)


def voice(notes, start=60):
    """Turn note numbers 0-11 into rising MIDI pitches, the first at or above `start` (60 = middle C)."""
    pitches = []
    for note in notes:
        pitch = start + (note - start) % 12
        while pitches and pitch <= pitches[-1]:
            pitch += 12
        pitches.append(pitch)
    return pitches


@lru_cache(maxsize=256)
def render_note(midi, length):
    f = frequency(midi)
    harmonics = [(2 * math.pi * f * h / RATE, amp) for h, amp in HARMONICS if f * h < RATE / 2]
    count = int(length * RATE)
    fade_start = count - int(FADE * RATE)
    samples = array("f", bytes(4 * count))
    for i in range(count):
        envelope = min(1.0, i / 100) * math.exp(-3 * i / RATE)
        if i > fade_start:
            envelope *= (count - i) / (count - fade_start)
        samples[i] = envelope * sum(amp * math.sin(step * i) for step, amp in harmonics)
    return samples


def render(events):
    """Mix (start seconds, midi pitch, length seconds) events into one list of samples."""
    end = max(start + length for start, _, length in events)
    mix = array("f", bytes(4 * int(end * RATE + 1)))
    for start, midi, length in events:
        offset = int(start * RATE)
        for i, value in enumerate(render_note(midi, length)):
            mix[offset + i] += value
    peak = max(map(abs, mix)) or 1
    return array("h", (int(v / peak * 0.8 * 32767) for v in mix))


class Player:
    """Plays events in the background; starting a new sound cuts off the previous one."""

    def __init__(self):
        self.folder = tempfile.mkdtemp(prefix="music_helper_")
        atexit.register(shutil.rmtree, self.folder, ignore_errors=True)
        self.lock = threading.Lock()
        self.generation = 0
        self.process = None

    def play(self, events):
        if not events:
            return
        self.generation += 1
        threading.Thread(target=self._play, args=(events, self.generation), daemon=True).start()

    def _play(self, events, generation):
        samples = render(events)
        with self.lock:
            if generation != self.generation:  # a newer sound was requested while this one rendered
                return
            path = os.path.join(self.folder, f"{generation}.wav")
            with wave.open(path, "wb") as file:
                file.setnchannels(1)
                file.setsampwidth(2)
                file.setframerate(RATE)
                file.writeframes(samples.tobytes())
            self._start(path)

    def _start(self, path):
        if sys.platform == "win32":
            import winsound
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            return
        if self.process:
            self.process.terminate()
        commands = ["afplay"] if sys.platform == "darwin" else ["paplay", "aplay"]
        command = next((c for c in commands if shutil.which(c)), None)
        if command:
            self.process = subprocess.Popen([command, path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
