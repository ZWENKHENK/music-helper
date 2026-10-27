NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLATS = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}

# Each chord/scale is a list of steps (in semitones) above the root note
CHORDS = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "maj7": [0, 4, 7, 11],
    "7": [0, 4, 7, 10],
    "min7": [0, 3, 7, 10],
    "min7b5": [0, 3, 6, 10],
}

SCALES = {
    "Ionian (major)": [0, 2, 4, 5, 7, 9, 11],
    "Dorian": [0, 2, 3, 5, 7, 9, 10],
    "Phrygian": [0, 1, 3, 5, 7, 8, 10],
    "Lydian": [0, 2, 4, 6, 7, 9, 11],
    "Mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "Aeolian (natural minor)": [0, 2, 3, 5, 7, 8, 10],
    "Locrian": [0, 1, 3, 5, 6, 8, 10],
    "Harmonic minor": [0, 2, 3, 5, 7, 8, 11],
}

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


def parse_notes(text):
    """Turn 'C E G' or 'c, eb, g' into a set of numbers."""
    notes = set()
    for word in text.replace(",", " ").split():
        name = FLATS.get(word.capitalize(), word.capitalize())
        if name not in NOTE_NAMES:
            raise ValueError(f"I don't recognise the note '{word}'")
        notes.add(NOTE_NAMES.index(name))
    return notes


def find_chords(notes):
    exact, fits_inside = [], []
    for root in range(12):
        for name, steps in CHORDS.items():
            chord = {(root + s) % 12 for s in steps}
            label = f"{NOTE_NAMES[root]} {name}"
            if chord == notes:
                exact.append(label)
            elif chord < notes:  # every chord note is in your notes
                fits_inside.append(label)
    return exact, fits_inside


def find_scales(notes):
    matches = []
    for root in range(12):
        for name, steps in SCALES.items():
            scale = {(root + s) % 12 for s in steps}
            if notes <= scale:  # all your notes are in this scale
                matches.append((root, name))
    return matches


def scale_chords(root, name):
    """Build a triad on every note of the scale by stacking thirds."""
    scale = [(root + s) % 12 for s in SCALES[name]]
    chords = []
    for i in range(len(scale)):
        triad = [scale[i], scale[(i + 2) % 7], scale[(i + 4) % 7]]
        shape = tuple((n - triad[0]) % 12 for n in triad)
        quality = TRIAD_NAMES.get(shape, "?")
        chords.append(f"{NOTE_NAMES[triad[0]]} {quality}")
    return chords


def main():
    text = input("Enter your notes (e.g. C E G A): ")
    try:
        notes = parse_notes(text)
    except ValueError as error:
        print(error)
        return

    exact, fits_inside = find_chords(notes)
    print("\nChords that match exactly:", exact or "none")
    print("Chords hiding inside your notes:", fits_inside or "none")

    scales = find_scales(notes)
    if not scales:
        print("\nNo scale or mode contains all of those notes.")
        return

    print("\nScales/modes that contain all your notes:")
    for number, (root, name) in enumerate(scales, start=1):
        print(f"  {number}. {NOTE_NAMES[root]} {name}")

    choice = int(input("\nPick one for chords and progressions: "))
    root, name = scales[choice - 1]
    chords = scale_chords(root, name)

    print(f"\nChords in {NOTE_NAMES[root]} {name}:")
    for degree, chord in enumerate(chords, start=1):
        print(f"  {degree}: {chord}")

    print("\nProgression ideas:")
    for prog in PROGRESSIONS:
        print("  " + " -> ".join(chords[d - 1] for d in prog))


main()