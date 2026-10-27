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

Type notes, or click keys on the piano or frets on the guitar neck to toggle them. Both show your notes (blue), the selected scale (green) and its root (orange). Pick a scale from the list to see its chords and progression ideas.

The guitar neck's tuning can be changed from the dropdown above it (standard, drop D, DADGAD, open tunings, 7-string, bass and more), or type your own from low string to high, e.g. `C G C F A D`, and press Enter. Anything from 4 to 8 strings works.
