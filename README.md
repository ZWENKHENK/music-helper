# ZWENKHENK's Chordspiel

Enter a set of notes and get back:

- chords that match them exactly, and chords contained within them
- scales and modes that contain all the notes: the major modes, harmonic and melodic minor and its modes, exotic scales (Phrygian dominant, double harmonic, Hungarian minor...), pentatonics, blues, whole tone and diminished
- the chords of a chosen scale with their Roman numerals (for pentatonic, blues and other scales that don't have 7 notes: the chords that fit in the scale)
- about 20 named chord progressions for the scale's key, from the pop axis (I V vi IV) and jazz ii–V–I to the Andalusian cadence and 12-bar blues, with chords borrowed from outside the scale marked *

## Usage

```
python music_helper.py
```

Notes can be written like `C E G A` or `c, eb, g` (sharps and flats both work).

## GUI

```
python music_helper_gui.py
```

Type notes, or click keys on the piano or frets on the guitar neck to toggle them. Both show your notes (blue), the selected scale (green) and its root (orange). Pick a scale from the list to see its chords and progression ideas. The **Show** dropdown above the list narrows it to one family of scales (major modes, melodic minor modes, pentatonic and blues...). Click any chord name to highlight it on the piano and guitar (purple); click it again to hide it. Click ▶ next to a progression to hear it while each chord lights up on the piano and guitar. Notes are spelled to fit the selected scale, so F major shows Bb rather than A#.

The guitar neck's tuning can be changed from the dropdown above it (standard, drop D, DADGAD, open tunings, 7-string, bass and more), or type your own from low string to high, e.g. `C G C F A D`, and press Enter. Anything from 4 to 8 strings works.

### Size

The **Size** dropdown (next to Sound) scales the whole window from 75% to 200%, on top of Windows' own display scaling. **Ctrl +** and **Ctrl −** step through the sizes and **Ctrl 0** goes back to 100%. The choice is remembered in `%APPDATA%\Chordspiel\settings.json`.

### Chord shapes

When a chord is selected, the guitar neck shows a playable shape for it in the current tuning, written the usual way (e.g. `x 3 2 0 1 0`, low string first). Use **‹ ›** to step through the shapes up the neck, or to "every position" to see all the chord's notes, and **▶ Play shape** to hear it strummed. Shapes are worked out for whatever tuning is set: the root is the lowest note, there are no muted strings in the middle, the stretch is at most four frets, and at most four fingers are needed (a barre counts as one).

### Sound

Clicking a piano key, a fret or a chord name plays it (untick **Play on click** to turn that off). **▶ Play** plays your notes, **▶ Play scale** plays the selected scale, and the ▶ in front of each progression plays it. The **Sound** dropdown picks where sound goes. On Windows it defaults to the built-in Microsoft GS Wavetable Synth, a General MIDI synth, and the **Instrument** dropdown chooses from 25 instruments (pianos, guitars, organs, strings, brass, pads...). Any other MIDI output, such as a hardware synth or a virtual port into a DAW, is listed too. **Built-in synth** is the app's own simple tone.

Sound needs no extra libraries: MIDI goes through Windows' `winmm`, and the built-in synth uses `winsound` on Windows, `afplay` on macOS and `paplay`/`aplay` on Linux.

## Web version

The same app runs in a web browser, with no install, at https://zwenkhenk.github.io/music-helper/ once GitHub Pages is switched on. The page lives in `docs/`: `theory.js` is the music theory ported from `music_helper.py`, `sound.js` makes the sound, and `app.js`, `index.html` and `style.css` make the window. To try it on your own computer, serve the `docs` folder with a local web server, e.g. `python -m http.server 8000 --directory docs`, then open http://localhost:8000. Opening `index.html` straight from the disk doesn't work in Chrome or Edge, because they block its modules.

The browser version uses the browser's own zoom (Ctrl + and Ctrl −) instead of the Size setting. Its built-in synth is made with the Web Audio API. Other sounds need a MIDI output that the browser can see, such as Windows' General MIDI synth. The browser may ask permission to use MIDI.

## Building the .exe

```
python -m venv .venv
.venv\Scripts\python -m pip install pyinstaller
.venv\Scripts\python -m PyInstaller --noconfirm --onefile --windowed --name "ZWENKHENK's Chordspiel" music_helper_gui.py
```

The app is written to `dist\ZWENKHENK's Chordspiel.exe`, a single file that runs without Python installed.
