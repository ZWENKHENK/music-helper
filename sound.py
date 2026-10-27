"""Sound output using only the standard library: a tiny synthesiser that renders notes to a WAV file,
and a MIDI player for Windows' built-in General MIDI synth or any connected MIDI device."""
import atexit
import ctypes
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import wave
from array import array
from functools import lru_cache

# General MIDI instruments to choose from, with their program numbers
INSTRUMENTS = {
    "Acoustic Grand Piano": 0,
    "Bright Piano": 1,
    "Electric Piano": 4,
    "Harpsichord": 6,
    "Vibraphone": 11,
    "Drawbar Organ": 16,
    "Church Organ": 19,
    "Accordion": 21,
    "Nylon Guitar": 24,
    "Steel Guitar": 25,
    "Clean Electric Guitar": 27,
    "Overdriven Guitar": 29,
    "Distortion Guitar": 30,
    "Acoustic Bass": 32,
    "Electric Bass": 33,
    "Violin": 40,
    "Harp": 46,
    "Strings": 48,
    "Choir": 52,
    "Trumpet": 56,
    "Brass Section": 61,
    "Alto Sax": 65,
    "Flute": 73,
    "New Age Pad": 88,
    "Warm Pad": 89,
}

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
        self.folder = tempfile.mkdtemp(prefix="chordspiel_")
        atexit.register(shutil.rmtree, self.folder, ignore_errors=True)
        self.lock = threading.Lock()
        self.generation = 0
        self.started = (0, 0.0)  # (generation, time.monotonic()) of the sound that last started playing
        self.process = None

    def play(self, events):
        """Start rendering and playing events; returns a number identifying this sound."""
        if not events:
            return None
        self.generation += 1
        threading.Thread(target=self._play, args=(events, self.generation), daemon=True).start()
        return self.generation

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
            self.started = (generation, time.monotonic())

    def set_program(self, program):
        pass  # the built-in synth has a single sound

    def close(self):
        pass

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


if sys.platform == "win32":
    from ctypes import wintypes

    class MIDIOUTCAPSW(ctypes.Structure):
        _fields_ = [("wMid", wintypes.WORD), ("wPid", wintypes.WORD), ("vDriverVersion", wintypes.UINT),
                    ("szPname", wintypes.WCHAR * 32), ("wTechnology", wintypes.WORD), ("wVoices", wintypes.WORD),
                    ("wNotes", wintypes.WORD), ("wChannelMask", wintypes.WORD), ("dwSupport", wintypes.DWORD)]

    winmm = ctypes.windll.winmm
    winmm.midiOutOpen.argtypes = [ctypes.POINTER(wintypes.HANDLE), wintypes.UINT, ctypes.c_size_t, ctypes.c_size_t, wintypes.DWORD]
    winmm.midiOutShortMsg.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    winmm.midiOutClose.argtypes = [wintypes.HANDLE]
else:
    winmm = None


def midi_outputs():
    """The MIDI outputs Windows knows about, as {name: device number}, e.g. 'Microsoft GS Wavetable Synth'."""
    outputs = {}
    if winmm:
        for device in range(winmm.midiOutGetNumDevs()):
            caps = MIDIOUTCAPSW()
            if winmm.midiOutGetDevCapsW(device, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
                outputs[caps.szPname] = device
    return outputs


class MidiPlayer:
    """Plays events through a MIDI output; starting a new sound cuts off the previous one."""

    def __init__(self, device, program=0):
        self.handle = wintypes.HANDLE()
        error = winmm.midiOutOpen(ctypes.byref(self.handle), device, 0, 0, 0)
        if error:
            raise OSError(f"Windows MIDI error {error}" + (" (it's in use by another program)" if error == 4 else ""))
        self.lock = threading.Lock()
        self.generation = 0
        self.started = (0, 0.0)
        self.set_program(program)

    def send(self, status, data1=0, data2=0):
        winmm.midiOutShortMsg(self.handle, status | data1 << 8 | data2 << 16)

    def set_program(self, program):
        self.send(0xC0, program)

    def notes_off(self):
        self.send(0xB0, 120)  # all sound off
        self.send(0xB0, 123)  # all notes off

    def close(self):
        self.generation += 1  # stops a sequence that is still playing
        with self.lock:
            self.notes_off()
            winmm.midiOutClose(self.handle)

    def play(self, events):
        """Start playing events; returns a number identifying this sound."""
        if not events:
            return None
        self.generation += 1
        threading.Thread(target=self._play, args=(events, self.generation), daemon=True).start()
        return self.generation

    def _play(self, events, generation):
        # Note-offs sort before note-ons at the same moment, so a repeated note sounds again
        messages = sorted([(start, 1, 0x90, pitch, 100) for start, pitch, _ in events] +
                          [(start + length, 0, 0x80, pitch, 0) for start, pitch, length in events])
        with self.lock:  # the previous sequence notices it was replaced and lets go within 10 ms
            if generation != self.generation:
                return
            self.notes_off()
            start = time.monotonic()
            self.started = (generation, start)
            for at, _, status, pitch, velocity in messages:
                while (wait := start + at - time.monotonic()) > 0 and generation == self.generation:
                    time.sleep(min(wait, 0.01))
                if generation != self.generation:
                    return
                self.send(status, pitch, velocity)
