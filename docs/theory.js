// Music theory, ported from music_helper.py. Notes are numbers 0-11 with C = 0.

export const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const LETTERS = "CDEFGAB";
const NATURALS = [0, 2, 4, 5, 7, 9, 11]; // semitone of each letter above C
const ACCIDENTALS = { "#": 1, "♯": 1, b: -1, "♭": -1 };
const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII"];
// The usual name for each root, used to break ties when spelling scales (Bb blues rather than A# blues)
export const USUAL_ROOTS = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"];

// Python's % always gives a result from 0 up, so JavaScript needs this instead
export function mod(a, n = 12) {
  return ((a % n) + n) % n;
}

// Each chord/scale is a list of steps (in semitones) above the root note. Maps keep the order.
export const CHORDS = new Map([
  ["major", [0, 4, 7]],
  ["minor", [0, 3, 7]],
  ["dim", [0, 3, 6]],
  ["aug", [0, 4, 8]],
  ["sus2", [0, 2, 7]],
  ["sus4", [0, 5, 7]],
  ["majb5", [0, 4, 6]],
  ["sus2b5", [0, 2, 6]],
  ["maj7", [0, 4, 7, 11]],
  ["7", [0, 4, 7, 10]],
  ["min7", [0, 3, 7, 10]],
  ["min7b5", [0, 3, 6, 10]],
]);

export const SCALE_FAMILIES = new Map([
  ["Major modes", new Map([
    ["Ionian (major)", [0, 2, 4, 5, 7, 9, 11]],
    ["Dorian", [0, 2, 3, 5, 7, 9, 10]],
    ["Phrygian", [0, 1, 3, 5, 7, 8, 10]],
    ["Lydian", [0, 2, 4, 6, 7, 9, 11]],
    ["Mixolydian", [0, 2, 4, 5, 7, 9, 10]],
    ["Aeolian (natural minor)", [0, 2, 3, 5, 7, 8, 10]],
    ["Locrian", [0, 1, 3, 5, 6, 8, 10]],
  ])],
  ["Harmonic and melodic", new Map([
    ["Harmonic minor", [0, 2, 3, 5, 7, 8, 11]],
    ["Melodic minor", [0, 2, 3, 5, 7, 9, 11]],
    ["Harmonic major", [0, 2, 4, 5, 7, 8, 11]],
  ])],
  ["Melodic minor modes", new Map([
    ["Dorian b2", [0, 1, 3, 5, 7, 9, 10]],
    ["Lydian augmented", [0, 2, 4, 6, 8, 9, 11]],
    ["Lydian dominant", [0, 2, 4, 6, 7, 9, 10]],
    ["Mixolydian b6", [0, 2, 4, 5, 7, 8, 10]],
    ["Locrian #2", [0, 2, 3, 5, 6, 8, 10]],
    ["Altered", [0, 1, 3, 4, 6, 8, 10]],
  ])],
  ["Exotic", new Map([
    ["Phrygian dominant", [0, 1, 4, 5, 7, 8, 10]],
    ["Double harmonic major", [0, 1, 4, 5, 7, 8, 11]],
    ["Hungarian minor", [0, 2, 3, 6, 7, 8, 11]],
    ["Neapolitan minor", [0, 1, 3, 5, 7, 8, 11]],
    ["Neapolitan major", [0, 1, 3, 5, 7, 9, 11]],
  ])],
  ["Pentatonic and blues", new Map([
    ["Major pentatonic", [0, 2, 4, 7, 9]],
    ["Minor pentatonic", [0, 3, 5, 7, 10]],
    ["Blues", [0, 3, 5, 6, 7, 10]],
    ["Major blues", [0, 2, 3, 4, 7, 9]],
    ["Hirajoshi", [0, 2, 3, 7, 8]],
    ["In sen", [0, 1, 5, 7, 10]],
  ])],
  ["Symmetric", new Map([
    ["Whole tone", [0, 2, 4, 6, 8, 10]],
    ["Diminished (half-whole)", [0, 1, 3, 4, 6, 7, 9, 10]],
    ["Diminished (whole-half)", [0, 2, 3, 5, 6, 8, 9, 11]],
  ])],
]);
export const SCALES = new Map([...SCALE_FAMILIES.values()].flatMap(family => [...family]));

// Well-known progressions in Roman numerals, counted from the key's home note along the major scale.
// Upper case is a major chord, lower case minor, ° diminished, + augmented and ø half-diminished;
// 7 or maj7 adds a seventh, and b or # moves the root down or up a semitone (bVII in C is Bb).
export const PROGRESSIONS = [
  ["Pop axis", "major", "I V vi IV", "The most-used progression in modern pop"],
  ["Doo-wop", "major", "I vi IV V", "The 1950s ballad progression"],
  ["Three-chord cadence", "major", "I IV V I", "The backbone of folk, country and rock and roll"],
  ["Axis from the minor chord", "major", "vi IV I V", "The pop axis started on vi for a moodier feel"],
  ["Jazz ii–V–I", "major", "ii7 V7 Imaj7", "The building block of jazz standards"],
  ["Turnaround", "major", "Imaj7 vi7 ii7 V7", "Loops back to the start in jazz and pop standards"],
  ["Circle of fifths", "major", "iii7 vi7 ii7 V7 Imaj7", "Each chord falls a fifth to the next"],
  ["Royal road", "major", "IVmaj7 V7 iii7 vi", "A favourite of Japanese pop"],
  ["Pachelbel's Canon", "major", "I V vi iii IV I IV V", "The baroque pattern behind countless songs"],
  ["Mixolydian rock", "major", "I bVII IV I", "Classic rock's flat-seven sound"],
  ["Plagal (Amen)", "major", "I IV I", "The gentle IV to I close of hymns"],
  ["Minor iv", "major", "I IV iv I", "Borrows a minor iv for a bittersweet turn"],
  ["12-bar blues", "major", "I7 I7 I7 I7 IV7 IV7 I7 I7 V7 IV7 I7 V7", "The blues form, one chord per bar"],
  ["Minor epic", "minor", "i bVI bIII bVII", "Big, cinematic minor-key pop and rock"],
  ["Andalusian cadence", "minor", "i bVII bVI V", "The descending flamenco progression"],
  ["Minor cadence", "minor", "i iv v i", "Natural minor's version of I IV V I"],
  ["Harmonic minor cadence", "minor", "i iv V i", "A major V pulls harder back home"],
  ["Minor ii–V–i", "minor", "iiø7 V7 i7", "Jazz's minor-key building block"],
  ["Dorian vamp", "minor", "i7 IV7", "The two-chord groove of funk and modal jazz"],
  ["Minor pop loop", "minor", "i bVII bVI bVII", "A rocking loop in natural minor"],
  ["12-bar minor blues", "minor", "i7 i7 i7 i7 iv7 iv7 i7 i7 bVI7 V7 i7 V7", "The blues form in a minor key"],
].map(([name, key, numerals, description]) => ({ name, key, numerals, description }));

const NUMERAL = /^([b#]?)(VII|VI|V|IV|III|II|I|vii|vi|v|iv|iii|ii|i)(°|\+|ø)?(maj7|7)?$/;
const NUMERAL_MARKS = { dim: "°", aug: "+", majb5: "(b5)", sus2b5: "sus2(b5)" };
// How many letters above the root each chord note is named with, e.g. a minor 3rd (3) is a third (2)
const CHORD_LETTERS = { 0: 0, 2: 1, 3: 2, 4: 2, 5: 3, 6: 4, 7: 4, 8: 4, 10: 6, 11: 6 };
// Lets us look up a chord name from its shape, e.g. "0,4,7" -> "major"
const TRIAD_NAMES = new Map([...CHORDS]
  .filter(([, steps]) => steps.length === 3)
  .map(([name, steps]) => [steps.join(","), name]));

export function noteValue(word) {
  const letter = word.slice(0, 1).toUpperCase(), accidentals = word.slice(1);
  if (letter.length !== 1 || !LETTERS.includes(letter) || [...accidentals].some(a => !(a in ACCIDENTALS))) {
    throw new Error(`I don't recognise the note '${word}'`);
  }
  return mod(NATURALS[LETTERS.indexOf(letter)] + [...accidentals].reduce((sum, a) => sum + ACCIDENTALS[a], 0));
}

// Turn 'C E G' or 'c, eb, g' into a Set of numbers
export function parseNotes(text) {
  return new Set(text.replace(/,/g, " ").split(/\s+/).filter(Boolean).map(noteValue));
}

// Name a note using the given letter plus whatever sharps or flats it needs
export function spell(note, letter) {
  const offset = mod(note - NATURALS[LETTERS.indexOf(letter)] + 6) - 6;
  return letter + (offset > 0 ? "#".repeat(offset) : "b".repeat(-offset));
}

// How many letters above the root's letter each scale note is named with.
// A 7-note scale uses each letter once. Other scales use the usual interval names
// (b3, 4, b5...), so the blues scale on C is C Eb F Gb G Bb.
export function letterSteps(steps) {
  if (steps.length === 7) return [0, 1, 2, 3, 4, 5, 6];
  const letters = { 0: 0, 1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 4, 7: 4, 8: 5, 9: 5, 10: 6, 11: 6 };
  if (!steps.includes(5)) letters[6] = 3; // #4 rather than b5 when there's no 4th, e.g. whole tone
  if (!steps.includes(7) && !steps.includes(9)) letters[8] = 4; // #5 rather than b6 when there's no 5th or 6th
  return steps.map(s => letters[s]);
}

function isLessThan(a, b) {
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return a[i] < b[i];
  }
  return false;
}

// Name each note of a scale so it reads well, e.g. F major gets Bb rather than A#.
// Tries every way of naming the root and keeps the one with the fewest accidentals,
// preferring the usual root name on a tie. Returns a Map of note number -> name.
export function spellScale(root, name) {
  const steps = SCALES.get(name);
  const offsets = letterSteps(steps);
  let best = null;
  for (let start = 0; start < LETTERS.length; start++) {
    if (spell(root, LETTERS[start]).length > 2) continue; // root would need a double sharp/flat
    const names = steps.map((s, i) => spell(mod(root + s), LETTERS[mod(start + offsets[i], 7)]));
    const score = [names.reduce((sum, n) => sum + n.length - 1, 0), names[0] !== USUAL_ROOTS[root] ? 1 : 0];
    if (best === null || isLessThan(score, best.score)) best = { score, names };
  }
  return new Map(steps.map((s, i) => [mod(root + s), best.names[i]]));
}

export function chordNotes(root, quality) {
  return CHORDS.get(quality).map(s => mod(root + s));
}

export function findChords(notes) {
  const exact = [], fitsInside = [];
  for (let root = 0; root < 12; root++) {
    for (const quality of CHORDS.keys()) {
      const chord = new Set(chordNotes(root, quality));
      if (chord.size === notes.size && [...chord].every(n => notes.has(n))) exact.push([root, quality]);
      else if (chord.size < notes.size && [...chord].every(n => notes.has(n))) fitsInside.push([root, quality]);
    }
  }
  return { exact, fitsInside };
}

// Every scale and mode that contains all of the notes, as [root, name] pairs
export function findScales(notes) {
  const matches = [];
  for (let root = 0; root < 12; root++) {
    for (const [name, steps] of SCALES) {
      const scale = new Set(steps.map(s => mod(root + s)));
      if ([...notes].every(n => scale.has(n))) matches.push([root, name]);
    }
  }
  return matches;
}

// For each note of the scale, every chord built on it that stays inside the scale.
// Used for scales that aren't 7 notes (pentatonic, blues...), where stacking thirds doesn't work.
export function fittingChords(root, name) {
  const scale = new Set(SCALES.get(name).map(s => mod(root + s)));
  return SCALES.get(name).map(s => {
    const note = mod(root + s);
    return [...CHORDS.keys()]
      .filter(q => chordNotes(note, q).every(n => scale.has(n)))
      .map(q => [note, q]);
  });
}

// Build a triad on every note of a 7-note scale by stacking thirds, as [root, quality] pairs
export function scaleChords(root, name) {
  const scale = SCALES.get(name).map(s => mod(root + s));
  return scale.map((_, i) => {
    const triad = [scale[i], scale[(i + 2) % 7], scale[(i + 4) % 7]];
    const shape = triad.map(n => mod(n - triad[0]));
    return [triad[0], TRIAD_NAMES.get(shape.join(","))];
  });
}

// 'major' if the scale has a major 3rd, otherwise 'minor': which progressions suit it
export function scaleKey(name) {
  return SCALES.get(name).includes(4) ? "major" : "minor";
}

// Turn a Roman numeral like 'V7', 'bVII' or 'iiø7' into [semitones above the tonic, chord quality]
export function parseNumeral(numeral) {
  const match = NUMERAL.exec(numeral);
  if (!match) throw new Error(`I don't recognise the chord numeral '${numeral}'`);
  const [, accidental, roman, mark, seventh] = match;
  const step = mod(NATURALS[ROMAN.indexOf(roman.toUpperCase())] + { b: -1, "#": 1, "": 0 }[accidental]);
  let quality;
  if (mark === "°") quality = "dim";
  else if (mark === "ø") quality = "min7b5";
  else if (mark === "+") quality = "aug";
  else if (roman === roman.toLowerCase()) quality = seventh ? "min7" : "minor";
  else quality = seventh || "major";
  return [step, quality];
}

// The [root, quality] chords of a progression like 'I V vi IV' in the key of `tonic`
export function progressionChords(tonic, numerals) {
  return numerals.trim().split(/\s+/).map(numeral => {
    const [step, quality] = parseNumeral(numeral);
    return [mod(tonic + step), quality];
  });
}

// Write a scale's chord as a Roman numeral, e.g. the chord on degree 3 of A minor (C major) is 'bIII'
export function romanNumeral(tonic, degree, chord) {
  const [root, quality] = chord;
  const offset = mod(root - tonic - NATURALS[degree] + 6) - 6;
  const lower = ["minor", "dim", "min7", "min7b5"].includes(quality);
  const numeral = lower ? ROMAN[degree].toLowerCase() : ROMAN[degree];
  const accidental = offset < 0 ? "b".repeat(-offset) : "#".repeat(offset);
  return accidental + numeral + (NUMERAL_MARKS[quality] || "");
}

// Name a chord's notes by stacking letters on its root, e.g. Ab major is Ab C Eb, not G# C D#
export function spellChord(rootName, quality) {
  const root = noteValue(rootName), start = LETTERS.indexOf(rootName[0]);
  return new Map(CHORDS.get(quality).map(s => {
    const note = mod(root + s);
    return [note, spell(note, LETTERS[mod(start + CHORD_LETTERS[s], 7)])];
  }));
}

// A shape can be played if it has enough strings, no muted strings between sounding ones, the root in the
// bass and every required note, a fret stretch within `span`, and at most four fingers. Frets are
// null for muted strings; `tuning` is low string first.
export function isPlayable(shape, tuning, root, required, minStrings, span) {
  const sounding = shape.flatMap((f, i) => (f === null ? [] : [i]));
  if (sounding.length < minStrings || sounding[sounding.length - 1] - sounding[0] + 1 !== sounding.length) {
    return false;
  }
  const notes = sounding.map(i => mod(tuning[i] + shape[i]));
  if (notes[0] !== root || ![...required].every(n => notes.includes(n))) return false;
  const fretted = shape.filter(f => f); // leaves out muted (null) and open (0) strings
  if (!fretted.length) return true;
  const low = Math.min(...fretted), high = Math.max(...fretted);
  if (high - low > span || (shape.includes(0) && high > 4)) return false; // too much of a stretch, or open strings far from the nut
  // The lowest fret can be a barre if it's on several strings with no open string in between
  const barre = shape.flatMap((f, i) => (f === low ? [i] : []));
  let fingers = fretted.length;
  if (barre.length > 1 && !shape.slice(barre[0], barre[barre.length - 1] + 1).includes(0)) {
    fingers = 1 + fretted.filter(f => f > low).length;
  }
  return fingers <= 4;
}

// Call visit(shape) for every combination of one choice from each list, reusing the same array
function forEachShape(options, visit) {
  const shape = [];
  const walk = i => {
    if (i === options.length) return visit(shape);
    for (const choice of options[i]) {
      shape[i] = choice;
      walk(i + 1);
    }
  };
  walk(0);
}

// Find practical shapes for a chord on a fretted instrument.
// `tuning` lists the open-string notes from the lowest string up. Each shape has a fret per string in the
// same order (0 = open, null = muted). Shapes are sorted from the nut up, and ones that are just a fuller
// shape minus some strings are left out.
export function guitarShapes(tuning, root, quality, frets = 12, span = 3) {
  const tones = new Set(chordNotes(root, quality));
  const required = new Set(tones);
  if (tones.size === 4 && CHORDS.get(quality).includes(7)) required.delete(mod(root + 7));
  const minStrings = Math.min(4, tuning.length - 1);

  const found = new Map();
  for (let low = 1; low <= frets - span; low++) {
    const window = [0];
    for (let f = low; f <= low + span; f++) window.push(f);
    const options = tuning.map(openNote => [null, ...window.filter(f => tones.has(mod(openNote + f)))]);
    forEachShape(options, shape => {
      if (isPlayable(shape, tuning, root, required, minStrings, span)) {
        const key = JSON.stringify(shape);
        if (!found.has(key)) found.set(key, [...shape]);
      }
    });
  }

  const shapes = [...found.values()];
  const containedIn = (shape, other) =>
    shape !== other && shape.every((f, i) => f === null || other[i] === f);
  const kept = shapes.filter(shape => !shapes.some(other => containedIn(shape, other)));
  const sortKey = shape => {
    const played = shape.filter(f => f !== null);
    return [Math.min(...played), -played.length, played.reduce((a, b) => a + b, 0)];
  };
  return kept.sort((a, b) => {
    const ka = sortKey(a), kb = sortKey(b);
    return isLessThan(ka, kb) ? -1 : isLessThan(kb, ka) ? 1 : 0;
  });
}

// Write a shape the usual way, e.g. 'x 3 2 0 1 0'
export function shapeText(shape) {
  return shape.map(f => (f === null ? "x" : String(f))).join(" ");
}
