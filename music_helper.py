import itertools

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
LETTERS = "CDEFGAB"
NATURALS = [0, 2, 4, 5, 7, 9, 11]  # semitone of each letter above C
ACCIDENTALS = {"#": 1, "♯": 1, "b": -1, "♭": -1}
# The usual name for each root, used to break ties when spelling scales (Bb blues rather than A# blues)
USUAL_ROOTS = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

# Each chord/scale is a list of steps (in semitones) above the root note
CHORDS = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "majb5": [0, 4, 6],
    "sus2b5": [0, 2, 6],
    "maj7": [0, 4, 7, 11],
    "7": [0, 4, 7, 10],
    "min7": [0, 3, 7, 10],
    "min7b5": [0, 3, 6, 10],
}

SCALE_FAMILIES = {
    "Major modes": {
        "Ionian (major)": [0, 2, 4, 5, 7, 9, 11],
        "Dorian": [0, 2, 3, 5, 7, 9, 10],
        "Phrygian": [0, 1, 3, 5, 7, 8, 10],
        "Lydian": [0, 2, 4, 6, 7, 9, 11],
        "Mixolydian": [0, 2, 4, 5, 7, 9, 10],
        "Aeolian (natural minor)": [0, 2, 3, 5, 7, 8, 10],
        "Locrian": [0, 1, 3, 5, 6, 8, 10],
    },
    "Harmonic and melodic": {
        "Harmonic minor": [0, 2, 3, 5, 7, 8, 11],
        "Melodic minor": [0, 2, 3, 5, 7, 9, 11],
        "Harmonic major": [0, 2, 4, 5, 7, 8, 11],
    },
    "Melodic minor modes": {
        "Dorian b2": [0, 1, 3, 5, 7, 9, 10],
        "Lydian augmented": [0, 2, 4, 6, 8, 9, 11],
        "Lydian dominant": [0, 2, 4, 6, 7, 9, 10],
        "Mixolydian b6": [0, 2, 4, 5, 7, 8, 10],
        "Locrian #2": [0, 2, 3, 5, 6, 8, 10],
        "Altered": [0, 1, 3, 4, 6, 8, 10],
    },
    "Exotic": {
        "Phrygian dominant": [0, 1, 4, 5, 7, 8, 10],
        "Double harmonic major": [0, 1, 4, 5, 7, 8, 11],
        "Hungarian minor": [0, 2, 3, 6, 7, 8, 11],
        "Neapolitan minor": [0, 1, 3, 5, 7, 8, 11],
        "Neapolitan major": [0, 1, 3, 5, 7, 9, 11],
    },
    "Pentatonic and blues": {
        "Major pentatonic": [0, 2, 4, 7, 9],
        "Minor pentatonic": [0, 3, 5, 7, 10],
        "Blues": [0, 3, 5, 6, 7, 10],
        "Major blues": [0, 2, 3, 4, 7, 9],
        "Hirajoshi": [0, 2, 3, 7, 8],
        "In sen": [0, 1, 5, 7, 10],
    },
    "Symmetric": {
        "Whole tone": [0, 2, 4, 6, 8, 10],
        "Diminished (half-whole)": [0, 1, 3, 4, 6, 7, 9, 10],
        "Diminished (whole-half)": [0, 2, 3, 5, 6, 8, 9, 11],
    },
}
SCALES = {name: steps for family in SCALE_FAMILIES.values() for name, steps in family.items()}

# Common progressions as scale degrees (1 = first chord of the scale)
PROGRESSIONS = [
    [1, 5, 6, 4],
    [1, 4, 5, 1],
    [1, 6, 4, 5],
    [2, 5, 1],
    [6, 4, 1, 5],
    [1, 4, 6, 5],
]

# Lets us look up a chord name from its shape, e.g. (0, 4, 7) -> "major"
TRIAD_NAMES = {tuple(v): k for k, v in CHORDS.items() if len(v) == 3}


def note_value(word):
    """Turn a note name like 'C', 'eb', 'F#' or 'Cb' into a number 0-11."""
    letter, accidentals = word[:1].upper(), word[1:]
    if letter not in LETTERS or any(a not in ACCIDENTALS for a in accidentals):
        raise ValueError(f"I don't recognise the note '{word}'")
    return (NATURALS[LETTERS.index(letter)] + sum(ACCIDENTALS[a] for a in accidentals)) % 12


def parse_notes(text):
    """Turn 'C E G' or 'c, eb, g' into a set of numbers."""
    return {note_value(word) for word in text.replace(",", " ").split()}


def spell(note, letter):
    """Name a note using the given letter plus whatever sharps or flats it needs."""
    offset = (note - NATURALS[LETTERS.index(letter)] + 6) % 12 - 6
    return letter + ("#" * offset if offset > 0 else "b" * -offset)


def letter_steps(steps):
    """How many letters above the root's letter each scale note is named with.

    A 7-note scale uses each letter once. Other scales use the usual interval names
    (b3, 4, b5...), so the blues scale on C is C Eb F Gb G Bb.
    """
    if len(steps) == 7:
        return list(range(7))
    letters = {0: 0, 1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 4, 7: 4, 8: 5, 9: 5, 10: 6, 11: 6}
    if 5 not in steps:
        letters[6] = 3  # #4 rather than b5 when there's no 4th, e.g. whole tone
    if 7 not in steps and 9 not in steps:
        letters[8] = 4  # #5 rather than b6 when there's no 5th or 6th, e.g. whole tone
    return [letters[s] for s in steps]


def spell_scale(root, name):
    """Name each note of a scale so it reads well, e.g. F major gets Bb rather than A#.

    Tries every way of naming the root (e.g. A# or Bb) and keeps the one with the fewest accidentals,
    preferring the usual root name on a tie. Returns a dict of note number -> name.
    """
    best = None
    steps = SCALES[name]
    letter_offsets = letter_steps(steps)
    for start, letter in enumerate(LETTERS):
        if len(spell(root, letter)) > 2:  # root would need a double sharp/flat
            continue
        names = [spell((root + s) % 12, LETTERS[(start + k) % 7]) for s, k in zip(steps, letter_offsets)]
        score = (sum(len(n) - 1 for n in names), names[0] != USUAL_ROOTS[root])
        if best is None or score < best[0]:
            best = (score, names)
    return {(root + s) % 12: n for s, n in zip(steps, best[1])}


def chord_notes(root, quality):
    return [(root + s) % 12 for s in CHORDS[quality]]


def chord_label(root, quality, names=NOTE_NAMES):
    return f"{names[root]} {quality}"


def find_chords(notes):
    """Return (exact, fits_inside) lists of (root, quality) chords."""
    exact, fits_inside = [], []
    for root in range(12):
        for quality in CHORDS:
            chord = set(chord_notes(root, quality))
            if chord == notes:
                exact.append((root, quality))
            elif chord < notes:  # every chord note is in your notes
                fits_inside.append((root, quality))
    return exact, fits_inside


def find_scales(notes):
    matches = []
    for root in range(12):
        for name, steps in SCALES.items():
            scale = {(root + s) % 12 for s in steps}
            if notes <= scale:  # all your notes are in this scale
                matches.append((root, name))
    return matches


def fitting_chords(root, name):
    """For each note of the scale, every chord built on it that stays inside the scale.

    Used for scales that aren't 7 notes (pentatonic, blues...), where stacking thirds doesn't work.
    """
    scale = [(root + s) % 12 for s in SCALES[name]]
    return [[(note, q) for q in CHORDS if set(chord_notes(note, q)) <= set(scale)] for note in scale]


def scale_chords(root, name):
    """Build a triad on every note of a 7-note scale by stacking thirds, as (root, quality) pairs."""
    scale = [(root + s) % 12 for s in SCALES[name]]
    chords = []
    for i in range(len(scale)):
        triad = [scale[i], scale[(i + 2) % 7], scale[(i + 4) % 7]]
        shape = tuple((n - triad[0]) % 12 for n in triad)
        chords.append((triad[0], TRIAD_NAMES[shape]))
    return chords


def is_playable(shape, tuning, root, required, min_strings, span):
    sounding = [i for i, f in enumerate(shape) if f is not None]
    if len(sounding) < min_strings or sounding[-1] - sounding[0] + 1 != len(sounding):
        return False  # too few strings, or a muted string in the middle
    notes = [(tuning[i] + shape[i]) % 12 for i in sounding]
    if notes[0] != root or not required <= set(notes):
        return False
    fretted = [f for f in shape if f]
    if not fretted:
        return True
    low, high = min(fretted), max(fretted)
    if high - low > span or (0 in shape and high > 4):
        return False  # too much of a stretch, or open strings far from the nut
    # The lowest fret can be a barre if it's on several strings with no open string in between
    barre = [i for i, f in enumerate(shape) if f == low]
    if len(barre) > 1 and 0 not in shape[barre[0]:barre[-1] + 1]:
        fingers = 1 + sum(f > low for f in fretted)
    else:
        fingers = len(fretted)
    return fingers <= 4


def guitar_shapes(tuning, root, quality, frets=12, span=3):
    """Find practical shapes for a chord on a fretted instrument.

    `tuning` lists the open-string notes from the lowest string up. Each shape is a tuple with
    a fret per string in the same order (0 = open, None = muted). Shapes have the root in the
    bass, every chord note (the 5th may be left out of four-note chords), no muted strings
    between sounding ones, a stretch of at most `span` frets, and need at most four fingers.
    Shapes are sorted from the nut up (fuller and lower shapes first at each position), and ones
    that are just a fuller shape minus some strings are left out.
    """
    tones = set(chord_notes(root, quality))
    required = set(tones)
    if len(tones) == 4 and 7 in CHORDS[quality]:
        required.discard((root + 7) % 12)
    min_strings = min(4, len(tuning) - 1)

    found = set()
    for low in range(1, frets - span + 1):
        window = [0, *range(low, low + span + 1)]
        options = [[None] + [f for f in window if (open_note + f) % 12 in tones] for open_note in tuning]
        for shape in itertools.product(*options):
            if is_playable(shape, tuning, root, required, min_strings, span):
                found.add(shape)

    def contained_in(shape, other):
        return shape != other and all(f is None or other[i] == f for i, f in enumerate(shape))

    shapes = [s for s in found if not any(contained_in(s, other) for other in found)]
    def sort_key(shape):
        played = [f for f in shape if f is not None]
        return min(played), -len(played), sum(played)

    return sorted(shapes, key=sort_key)


def shape_text(shape):
    """Write a shape the usual way, e.g. 'x 3 2 0 1 0'."""
    return " ".join("x" if f is None else str(f) for f in shape)


def main():
    text = input("Enter your notes (e.g. C E G A): ")
    try:
        notes = parse_notes(text)
    except ValueError as error:
        print(error)
        return

    exact, fits_inside = find_chords(notes)
    print("\nChords that match exactly:", [chord_label(*c) for c in exact] or "none")
    print("Chords hiding inside your notes:", [chord_label(*c) for c in fits_inside] or "none")

    scales = find_scales(notes)
    if not scales:
        print("\nNo scale or mode contains all of those notes.")
        return

    print("\nScales/modes that contain all your notes:")
    for number, (root, name) in enumerate(scales, start=1):
        print(f"  {number}. {spell_scale(root, name)[root]} {name}")

    choice = int(input("\nPick one for chords and progressions: "))
    root, name = scales[choice - 1]
    spelling = spell_scale(root, name)
    if len(SCALES[name]) != 7:
        print(f"\nChords that fit in {spelling[root]} {name}:")
        for degree, chords in enumerate(fitting_chords(root, name), start=1):
            print(f"  {degree}: {', '.join(chord_label(r, q, spelling) for r, q in chords) or '-'}")
        return
    chords = [chord_label(r, q, spelling) for r, q in scale_chords(root, name)]

    print(f"\nChords in {spelling[root]} {name}:")
    for degree, chord in enumerate(chords, start=1):
        print(f"  {degree}: {chord}")

    print("\nProgression ideas:")
    for prog in PROGRESSIONS:
        print("  " + " -> ".join(chords[d - 1] for d in prog))


if __name__ == "__main__":
    main()