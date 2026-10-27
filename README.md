# music-helper

Enter a set of notes and get back:

- chords that match them exactly, and chords contained within them
- scales and modes that contain all the notes
- the chords of a chosen scale, plus common progression ideas

## Usage

```
python music_helper.py
```

Notes can be written like `C E G A` or `c, eb, g` (sharps and flats both work).

## GUI

```
python music_helper_gui.py
```

Type notes, or click keys on the piano or frets on the guitar neck to toggle them. Both show your notes (blue), the selected scale (green) and its root (orange). Pick a scale from the list to see its chords and progression ideas. Click any chord name to highlight it on the piano and guitar (purple); click it again to hide it. Notes are spelled to fit the selected scale, so F major shows Bb rather than A#.

The guitar neck's tuning can be changed from the dropdown above it (standard, drop D, DADGAD, open tunings, 7-string, bass and more), or type your own from low string to high, e.g. `C G C F A D`, and press Enter. Anything from 4 to 8 strings works.

### Sound

Clicking a piano key, a fret or a chord name plays it (untick **Play on click** to turn that off). **▶ Play** plays your notes, **▶ Play scale** plays the selected scale, and the ▶ in front of each progression plays it. Sound needs no extra libraries: it uses `winsound` on Windows, `afplay` on macOS and `paplay`/`aplay` on Linux.
