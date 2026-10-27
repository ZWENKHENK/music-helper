# ZWENKHENK's Chordspiel

Enter a set of notes and get back:

- chords that match them exactly, and chords contained within them
- scales and modes that contain all the notes: the major modes, harmonic and melodic minor and its modes, exotic scales (Phrygian dominant, double harmonic, Hungarian minor...), pentatonics, blues, whole tone and diminished
- the chords of a chosen scale, plus common progression ideas (for pentatonic, blues and other scales that don't have 7 notes: the chords that fit in the scale)

## Usage

```
python music_helper.py
```

Notes can be written like `C E G A` or `c, eb, g` (sharps and flats both work).

## GUI

```
python music_helper_gui.py
```

Type notes, or click keys on the piano or frets on the guitar neck to toggle them. Both show your notes (blue), the selected scale (green) and its root (orange). Pick a scale from the list to see its chords and progression ideas. The **Show** dropdown above the list narrows it to one family of scales (major modes, melodic minor modes, pentatonic and blues...). Click any chord name to highlight it on the piano and guitar (purple); click it again to hide it. Notes are spelled to fit the selected scale, so F major shows Bb rather than A#.

The guitar neck's tuning can be changed from the dropdown above it (standard, drop D, DADGAD, open tunings, 7-string, bass and more), or type your own from low string to high, e.g. `C G C F A D`, and press Enter. Anything from 4 to 8 strings works.

### Chord shapes

When a chord is selected, the guitar neck shows a playable shape for it in the current tuning, written the usual way (e.g. `x 3 2 0 1 0`, low string first). Use **‹ ›** to step through the shapes up the neck, or to "every position" to see all the chord's notes, and **▶ Play shape** to hear it strummed. Shapes are worked out for whatever tuning is set: the root is the lowest note, there are no muted strings in the middle, the stretch is at most four frets, and at most four fingers are needed (a barre counts as one).

### Sound

Clicking a piano key, a fret or a chord name plays it (untick **Play on click** to turn that off). **▶ Play** plays your notes, **▶ Play scale** plays the selected scale, and the ▶ in front of each progression plays it. Sound needs no extra libraries: it uses `winsound` on Windows, `afplay` on macOS and `paplay`/`aplay` on Linux.

## Building the .exe

```
python -m venv .venv
.venv\Scripts\python -m pip install pyinstaller
.venv\Scripts\python -m PyInstaller --noconfirm --onefile --windowed --name "ZWENKHENK's Chordspiel" music_helper_gui.py
```

The app is written to `dist\ZWENKHENK's Chordspiel.exe`, a single file that runs without Python installed.
