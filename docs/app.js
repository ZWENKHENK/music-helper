// The web version of the Chordspiel window, ported from music_helper_gui.py
import {
  NOTE_NAMES, PROGRESSIONS, SCALE_FAMILIES, SCALES, USUAL_ROOTS,
  chordNotes, findChords, findScales, fittingChords, guitarShapes, mod, parseNotes,
  progressionChords, romanNumeral, scaleChords, scaleKey, shapeText, spellChord, spellScale,
} from "./theory.js";
import { INSTRUMENTS, MidiPlayer, SynthPlayer, midiOutputs, voice } from "./sound.js";

// Colours, matching the desktop app's dark theme
const NOTE_COLOR = "#3b82f6";
const SCALE_COLOR = "#86efac";
const CHORD_COLOR = "#c084fc";
const ROOT_COLOR = "#f97316";
const BG = "#1e1f22";
const PANEL = "#2b2d31";
const BORDER = "#3f4248";
const MUTED = "#949ba4";
const TEXT_ON = { [NOTE_COLOR]: "white", [SCALE_COLOR]: "#14532d", [CHORD_COLOR]: "#2e1065" };

// Piano layout: semitones of the white keys, and which white key each black key follows
const WHITE_STEPS = [0, 2, 4, 5, 7, 9, 11];
const BLACK_AFTER = { 0: 1, 1: 3, 3: 6, 4: 8, 5: 10 }; // white index in octave -> black note
const OCTAVES = 2;
const WHITE_W = 36, WHITE_H = 130;
const BLACK_W = 22, BLACK_H = 80;
const PIANO_START = 60; // the piano's lowest C is middle C

// Guitar tunings, written low string to high; the neck draws the high string at the top like tab
const TUNINGS = {
  "Standard": "E A D G B E",
  "Half step down": "Eb Ab Db Gb Bb Eb",
  "Drop D": "D A D G B E",
  "D Standard": "D G C F A D",
  "Drop C": "C G C F A D",
  "DADGAD": "D A D G A D",
  "Open G": "D G D G B D",
  "Open D": "D A D F# A D",
  "Open E": "E B E G# B E",
  "7-string": "B E A D G B E",
  "Bass": "E A D G",
};
const MIN_STRINGS = 4, MAX_STRINGS = 8;
const FRETS = 12;
const NUT_X = 44, FRET_W = 52, STRING_GAP = 26, TOP = 18;
const FRET_MARKERS = [3, 5, 7, 9];
const LOWEST_STRING = 40; // E2, a guitar's low E; other tunings put their lowest string as near to this as possible

const CHORD_LENGTH = 1.6, SCALE_STEP = 0.3, PROGRESSION_STEP = 0.9; // seconds
const CHORD_HINT = "Click a chord name to show it on the piano and guitar.";
const ALL_SCALES = "All scales";
const BUILT_IN_SYNTH = "Built-in synth";
const WINDOWS_SYNTH = "Microsoft GS Wavetable Synth"; // Windows' own General MIDI synth, picked by default when present
const SVG_NS = "http://www.w3.org/2000/svg";

const $ = id => document.getElementById(id);
const playOnClick = () => $("play-on-click").checked;

const state = {
  notes: new Set(),
  exact: [],
  fitsInside: [],
  allScales: [], // every scale containing the notes
  scales: [], // the ones shown, after the family filter
  selectedScale: null, // [root, name]
  selectedChord: null, // [root, quality]
  spelling: new Map(), // note number -> name, from the selected scale
  chordSpelling: new Map(), // note number -> name, from the selected chord
  timers: [], // pending highlights while a progression plays
  strings: [], // tuning, high string first
  stringPitches: [], // each open string's actual pitch, high string first
  shapes: [], // guitar shapes for the selected chord, low string first
  shapeIndex: null, // which shape is on the neck; null shows every position
  shapesKey: null, // the chord and tuning the shapes were found for
};

const synth = new SynthPlayer();
let player = synth;
let midiOutputList = new Map(); // name -> MIDI output

// --- Small helpers ---

function el(tag, attrs = {}, text) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
}

function sameScale(a, b) {
  return a[0] === b[0] && a[1] === b[1];
}

function chordKey([root, quality]) {
  return `${root}:${quality}`;
}

function rootName(note) {
  return state.spelling.get(note) ?? USUAL_ROOTS[note];
}

// Name a note using the selected chord's spelling, then the scale's, then the usual name
function nameOf(note) {
  return state.chordSpelling.get(note) ?? rootName(note);
}

function chordName([root, quality]) {
  return `${rootName(root)} ${quality}`;
}

function noteStyle(note) {
  let scaleNotes = new Set(), chord = new Set(), root = null;
  if (state.selectedScale) {
    const [scaleRoot, name] = state.selectedScale;
    scaleNotes = new Set(SCALES.get(name).map(s => mod(scaleRoot + s)));
  }
  if (state.selectedChord) {
    root = state.selectedChord[0];
    chord = new Set(chordNotes(...state.selectedChord));
  }
  let fill = null;
  if (chord.has(note)) fill = CHORD_COLOR;
  else if (state.notes.has(note)) fill = NOTE_COLOR;
  else if (scaleNotes.has(note)) fill = SCALE_COLOR;
  return { fill, isRoot: note === root };
}

function notesFromInput() {
  try {
    return parseNotes($("notes").value);
  } catch {
    return new Set();
  }
}

// --- Note input ---

function press(note, pitch) {
  if (playOnClick()) play([[0, pitch, CHORD_LENGTH]]);
  toggleNote(note);
}

function toggleNote(note) {
  const notes = notesFromInput();
  if (notes.has(note)) notes.delete(note);
  else notes.add(note);
  const sorted = [...notes].sort((a, b) => a - b);
  $("notes").value = sorted.map(n => NOTE_NAMES[n]).join(" ");
  analyze();
  // Respell with the scale that was just picked, e.g. "A# D F" becomes "Bb D F"
  $("notes").value = sorted.map(n => nameOf(n)).join(" ");
}

function clear() {
  $("notes").value = "";
  $("error").textContent = "";
  state.notes = new Set();
  state.exact = [];
  state.fitsInside = [];
  state.allScales = [];
  fillScaleList();
}

function analyze() {
  const text = $("notes").value;
  if (!text.trim()) {
    clear();
    return;
  }
  try {
    state.notes = parseNotes(text);
  } catch (error) {
    $("error").textContent = error.message;
    return;
  }
  $("error").textContent = "";
  ({ exact: state.exact, fitsInside: state.fitsInside } = findChords(state.notes));
  state.allScales = findScales(state.notes);
  state.selectedScale = null; // so the first matching scale gets picked
  fillScaleList();
}

// Show the matching scales in the chosen family, keeping the selected scale if it's still listed
function fillScaleList() {
  stopAnimation();
  const family = $("family").value;
  const all = state.allScales;
  if (family === ALL_SCALES) {
    state.scales = all;
  } else {
    state.scales = all.filter(([, name]) => SCALE_FAMILIES.get(family).has(name));
  }
  let count = "";
  if (state.notes.size) {
    count = family === ALL_SCALES ? ` (${state.scales.length})` : ` (${state.scales.length} of ${all.length})`;
  }
  $("scales-heading").textContent = "Scales containing your notes" + count;

  const list = $("scale-list");
  list.replaceChildren(...state.scales.map(([root, name]) => new Option(`${spellScale(root, name).get(root)} ${name}`)));
  const index = state.selectedScale ? state.scales.findIndex(s => sameScale(s, state.selectedScale)) : -1;
  if (index >= 0) {
    list.selectedIndex = index;
  } else if (state.scales.length) {
    list.selectedIndex = 0;
    showScale();
  } else {
    state.selectedScale = null;
    state.selectedChord = null;
    state.spelling = new Map();
    renderResults();
    drawVisuals();
  }
}

function showScale() {
  const index = $("scale-list").selectedIndex;
  if (index < 0) return;
  stopAnimation();
  state.selectedScale = state.scales[index];
  state.selectedChord = null;
  state.spelling = spellScale(...state.selectedScale);
  renderResults();
  drawVisuals();
}

// --- Results text, with clickable chords ---

function chordLink(chord) {
  const span = document.createElement("span");
  span.className = "chord";
  span.dataset.chord = chordKey(chord);
  span.textContent = chordName(chord);
  span.tabIndex = 0;
  span.setAttribute("role", "button");
  span.addEventListener("click", () => selectChord(chord));
  return span;
}

function playLink(play) {
  const span = document.createElement("span");
  span.className = "chord";
  span.textContent = "▶ ";
  span.tabIndex = 0;
  span.setAttribute("role", "button");
  span.setAttribute("aria-label", "Play");
  span.addEventListener("click", play);
  return span;
}

// Build one piece of a results box: a string, { style, text }, { play }, { chord } or { block: [...] }
function toNode(part) {
  if (typeof part === "string") return document.createTextNode(part);
  if (part.style) {
    const span = document.createElement("span");
    span.className = part.style;
    span.textContent = part.text;
    return span;
  }
  if (part.play) return playLink(part.play);
  if (part.chord) return chordLink(part.chord);
  const line = document.createElement("div");
  line.className = "line";
  line.append(...part.block.map(toNode));
  return line;
}

function fill(container, parts) {
  container.replaceChildren(...parts.map(toNode));
}

function chordList(chords) {
  if (!chords.length) return ["none"];
  const parts = [];
  chords.forEach((chord, i) => {
    if (i) parts.push(", ");
    parts.push({ chord });
  });
  return parts;
}

function renderResults() {
  const hasNotes = state.notes.size > 0;
  fill($("exact"), hasNotes ? chordList(state.exact) : ["-"]);
  fill($("inside"), hasNotes ? chordList(state.fitsInside) : ["-"]);

  if (!state.selectedScale) {
    let title;
    if (state.allScales.length) title = "No scale in this family contains all of those notes.";
    else if (hasNotes) title = "No scale or mode contains all of those notes.";
    else title = "Pick a scale to see its chords";
    $("scale-title").textContent = title;
    fill($("details"), []);
  } else {
    const [root, name] = state.selectedScale;
    const parts = [];
    if (SCALES.get(name).length === 7) {
      $("scale-title").textContent = `Chords in ${rootName(root)} ${name}`;
      scaleChords(root, name).forEach((chord, degree) => {
        parts.push({ block: [{ style: "degree", text: romanNumeral(root, degree, chord) }, { chord }] });
      });
    } else {
      $("scale-title").textContent = `Chords that fit in ${rootName(root)} ${name}`;
      fittingChords(root, name).forEach((chords, index) => {
        parts.push(`${index + 1}: `, ...(chords.length ? chordList(chords) : ["-"]), "\n");
      });
    }
    parts.push(...progressionParts(root, name));
    fill($("details"), parts);
  }
  updateChordHighlight();
}

// The progressions for the scale's key, those that stay inside the scale first
function progressionParts(root, name) {
  const key = scaleKey(name);
  const scaleNotes = new Set(SCALES.get(name).map(s => mod(root + s)));
  const inside = [], borrowing = [];
  for (const prog of PROGRESSIONS) {
    if (prog.key !== key) continue;
    const chords = progressionChords(root, prog.numerals);
    const fits = chords.every(chord => chordNotes(...chord).every(n => scaleNotes.has(n)));
    (fits ? inside : borrowing).push([prog, chords]);
  }

  const parts = [
    { style: "heading", text: `\nProgressions in ${rootName(root)} ${key}\n` },
    { style: "muted", text: "Click ▶ to hear one and watch it on the piano and guitar.\n\n" },
  ];
  for (const [heading, progressions] of [[null, inside], ["Borrowing chords from outside the scale (*)", borrowing]]) {
    if (heading && progressions.length) parts.push({ style: "heading", text: `${heading}\n\n` });
    for (const [prog, chords] of progressions) {
      parts.push({ play: () => playProgression(chords, true) }, { style: "bold", text: prog.name },
        { style: "muted", text: `    ${prog.numerals}\n` });
      chords.forEach((chord, i) => {
        if (i) parts.push(" → ");
        parts.push({ chord });
        if (!chordNotes(...chord).every(n => scaleNotes.has(n))) parts.push("*");
      });
      parts.push({ style: "muted", text: `\n${prog.description}\n\n` });
    }
  }
  return parts;
}

function selectChord(chord) {
  stopAnimation();
  const same = state.selectedChord && chordKey(state.selectedChord) === chordKey(chord);
  state.selectedChord = same ? null : chord;
  updateChordHighlight();
  drawVisuals();
  if (state.selectedChord && playOnClick()) playShape();
}

// Highlight a chord without playing it, while a progression plays
function showChord(chord) {
  state.selectedChord = chord;
  updateChordHighlight();
  drawVisuals();
}

function updateChordHighlight() {
  state.chordSpelling = state.selectedChord
    ? spellChord(rootName(state.selectedChord[0]), state.selectedChord[1])
    : new Map();
  const selected = state.selectedChord ? chordKey(state.selectedChord) : null;
  for (const span of document.querySelectorAll(".results [data-chord]")) {
    span.classList.toggle("on", span.dataset.chord === selected);
  }
  if (state.selectedChord) {
    const names = chordNotes(...state.selectedChord).map(n => nameOf(n)).join(" ");
    $("chord-status").textContent = `Showing ${chordName(state.selectedChord)}: ${names}. Click it again to hide.`;
  } else {
    $("chord-status").textContent = CHORD_HINT;
  }
  updateShapes();
}

// --- Guitar chord shapes ---

// Find shapes for the selected chord in the current tuning, starting again at the first one
function updateShapes() {
  const key = JSON.stringify([state.selectedChord, state.strings]);
  if (key === state.shapesKey) return;
  state.shapesKey = key;
  state.shapes = state.selectedChord
    ? guitarShapes([...state.strings].reverse(), state.selectedChord[0], state.selectedChord[1], FRETS)
    : [];
  state.shapeIndex = state.shapes.length ? 0 : null;
  updateShapeLabel();
}

function currentShape() {
  return state.shapeIndex === null ? null : state.shapes[state.shapeIndex];
}

function updateShapeLabel() {
  let text;
  if (!state.selectedChord) {
    text = "click a chord name to see guitar shapes";
  } else if (!state.shapes.length) {
    text = `no practical ${chordName(state.selectedChord)} shapes in this tuning`;
  } else if (state.shapeIndex === null) {
    text = `${chordName(state.selectedChord)}: every position`;
  } else {
    const shape = shapeText(currentShape());
    text = `${chordName(state.selectedChord)}: ${shape}   (${state.shapeIndex + 1} of ${state.shapes.length})`;
  }
  $("shape-label").textContent = text;
  for (const button of [$("previous-shape"), $("next-shape"), $("play-shape")]) {
    button.disabled = !state.shapes.length;
  }
}

// Move through the shapes, with "every position" between the last and the first
function stepShape(step) {
  const positions = [null, ...state.shapes.map((_, i) => i)];
  state.shapeIndex = positions[mod(positions.indexOf(state.shapeIndex) + step, positions.length)];
  updateShapeLabel();
  drawGuitar();
  if (state.shapeIndex !== null && playOnClick()) playShape();
}

// Strum the shape on the neck from the low string up, or play the chord if no shape is shown
function playShape() {
  const shape = currentShape();
  if (!shape) {
    if (state.selectedChord) playProgression([state.selectedChord]);
    return;
  }
  const lowPitches = [...state.stringPitches].reverse();
  const pitches = shape.flatMap((f, i) => (f === null ? [] : [lowPitches[i] + f]));
  play(pitches.map((pitch, j) => [j * 0.04, pitch, CHORD_LENGTH]));
}

// --- Playback ---

// Play a sound, cutting off any progression that is still being followed on screen
function play(events) {
  stopAnimation();
  return player.play(events);
}

function playPreview() {
  if (playOnClick()) {
    play([48, 55, 60, 64, 67].map((pitch, i) => [i * 0.04, pitch, CHORD_LENGTH]));
  }
}

function playNotes() {
  const pitches = voice([...state.notes].sort((a, b) => a - b));
  const events = pitches.map((pitch, i) => [i * SCALE_STEP, pitch, SCALE_STEP * 1.5]);
  const start = pitches.length * SCALE_STEP;
  play([...events, ...pitches.map(pitch => [start, pitch, CHORD_LENGTH])]);
}

function playScale() {
  if (!state.selectedScale) return;
  const [root, name] = state.selectedScale;
  const notes = [...SCALES.get(name)].map(s => mod(root + s)).concat(root);
  const pitches = voice(notes);
  play(pitches.map((pitch, i) => [i * SCALE_STEP, pitch, SCALE_STEP * 1.5]));
}

// Play chords one after another, each strummed slightly from the root up.
// With `follow`, each chord is highlighted on the piano, guitar and in the text as it sounds.
function playProgression(chords, follow = false) {
  const events = [];
  chords.forEach((chord, i) => {
    const length = i === chords.length - 1 ? CHORD_LENGTH : PROGRESSION_STEP;
    voice(chordNotes(...chord)).forEach((pitch, j) => {
      events.push([i * PROGRESSION_STEP + j * 0.03, pitch, length]);
    });
  });
  const generation = play(events);
  if (follow) followPlayback(generation, chords);
}

function followPlayback(generation, chords) {
  if (generation === null || player.generation !== generation) return; // another sound replaced this one
  chords.forEach((chord, i) => {
    const delay = (player.startTime + i * PROGRESSION_STEP - player.now()) * 1000;
    state.timers.push(setTimeout(() => showChord(chord), Math.max(0, delay)));
  });
}

function stopAnimation() {
  state.timers.forEach(clearTimeout);
  state.timers = [];
}

function setOutput(preview = true) {
  stopAnimation();
  if (player !== synth) player.stop();
  player = synth;
  const name = $("output").value;
  if (name !== BUILT_IN_SYNTH) {
    try {
      player = new MidiPlayer(midiOutputList.get(name), INSTRUMENTS.get($("instrument").value));
    } catch {
      $("error").textContent = `Couldn't open ${name}. Using the built-in synth.`;
      $("output").value = BUILT_IN_SYNTH;
    }
  }
  // The built-in synth has one sound; instruments only apply to MIDI
  $("instrument").disabled = player === synth;
  if (preview) playPreview();
}

function setInstrument() {
  player.setProgram(INSTRUMENTS.get($("instrument").value));
  playPreview();
}

// --- Guitar tuning ---

function tuningLabel(name) {
  return `${name} (${TUNINGS[name]})`;
}

// Turn 'E A D G B E' (low to high) into note numbers, high string first
function parseTuning(text) {
  const strings = text.trim().split(/[\s,]+/).filter(Boolean).map(word => [...parseNotes(word)][0]);
  if (strings.length < MIN_STRINGS || strings.length > MAX_STRINGS) {
    throw new Error(`A tuning needs ${MIN_STRINGS} to ${MAX_STRINGS} strings`);
  }
  return strings.reverse();
}

// Store a tuning (high string first) and work out each open string's actual pitch.
// The lowest string is put as close as possible to the `lowest` pitch, and each string above it is higher.
function setStrings(strings, lowest = LOWEST_STRING) {
  state.strings = strings;
  const lowFirst = [...strings].reverse();
  lowest += mod(lowFirst[0] - lowest + 6) - 6;
  state.stringPitches = voice(lowFirst, lowest).reverse();
}

function setTuning() {
  let text = $("tuning").value.trim();
  let lowest = LOWEST_STRING;
  for (const name of Object.keys(TUNINGS)) {
    if (text === name || text === tuningLabel(name)) {
      text = TUNINGS[name];
      if (name === "Bass") lowest -= 12; // bass strings sound an octave below a guitar's
    }
  }
  try {
    setStrings(parseTuning(text), lowest);
  } catch (error) {
    $("tuning-error").textContent = error.message;
    return;
  }
  $("tuning-error").textContent = "";
  // Show the matching preset, or Custom if none matches
  $("tuning-preset").value = Object.keys(TUNINGS).find(name => TUNINGS[name] === text) ?? "";
  updateShapes();
  drawGuitar();
}

// --- Drawing ---

function drawVisuals() {
  drawPiano();
  drawGuitar();
}

function drawPiano() {
  const svg = $("piano");
  const width = WHITE_W * 7 * OCTAVES, height = WHITE_H + 1;
  svg.replaceChildren();
  svg.setAttribute("width", width);
  svg.setAttribute("height", height);
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

  for (let i = 0; i < 7 * OCTAVES; i++) {
    const note = WHITE_STEPS[i % 7];
    const x = i * WHITE_W;
    const pitch = PIANO_START + 12 * Math.floor(i / 7) + note;
    const { fill, isRoot } = noteStyle(note);
    const key = el("g", { class: "key", "data-note": note, "data-pitch": pitch });
    key.append(el("rect", { x, y: 0, width: WHITE_W, height: WHITE_H, fill: fill || "#ececec", stroke: BG }));
    key.append(el("text", {
      x: x + WHITE_W / 2, y: WHITE_H - 14, "text-anchor": "middle", "dominant-baseline": "central",
      fill: TEXT_ON[fill] || "#555", "font-size": 9, "font-weight": fill ? "bold" : "normal",
    }, nameOf(note)));
    if (isRoot) key.append(el("circle", { cx: x + WHITE_W / 2, cy: WHITE_H - 35, r: 5, fill: ROOT_COLOR }));
    svg.append(key);
  }

  for (let i = 0; i < 7 * OCTAVES; i++) {
    if (!(i % 7 in BLACK_AFTER)) continue;
    const note = BLACK_AFTER[i % 7];
    const x = (i + 1) * WHITE_W - BLACK_W / 2;
    const pitch = PIANO_START + 12 * Math.floor(i / 7) + note;
    const { fill, isRoot } = noteStyle(note);
    const key = el("g", { class: "key", "data-note": note, "data-pitch": pitch });
    key.append(el("rect", { x, y: 0, width: BLACK_W, height: BLACK_H, fill: fill || "#18181b", stroke: BG }));
    if (fill) {
      key.append(el("text", {
        x: x + BLACK_W / 2, y: BLACK_H - 12, "text-anchor": "middle", "dominant-baseline": "central",
        fill: TEXT_ON[fill], "font-size": 7, "font-weight": "bold",
      }, nameOf(note)));
    }
    if (isRoot) key.append(el("circle", { cx: x + BLACK_W / 2, cy: BLACK_H - 30, r: 4, fill: ROOT_COLOR }));
    svg.append(key);
  }
}

function fretX(fret) {
  // Centre x of a fret position; fret 0 (open string) sits left of the nut
  return fret === 0 ? NUT_X / 2 : NUT_X + (fret - 0.5) * FRET_W;
}

function drawGuitar() {
  const svg = $("guitar");
  const bottom = TOP + STRING_GAP * (state.strings.length - 1);
  const right = NUT_X + FRET_W * FRETS;
  const width = NUT_X + FRET_W * FRETS + 10, height = bottom + 40;
  svg.replaceChildren();
  svg.setAttribute("width", width);
  svg.setAttribute("height", height);
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

  svg.append(el("rect", { x: NUT_X, y: TOP, width: right - NUT_X, height: bottom - TOP, fill: "#5c4330" }));
  const mid = (TOP + bottom) / 2;
  for (const fret of FRET_MARKERS) svg.append(el("circle", { cx: fretX(fret), cy: mid, r: 5, fill: "#8a6a4a" }));
  for (const y of [TOP + STRING_GAP * 1.5, bottom - STRING_GAP * 1.5]) {
    svg.append(el("circle", { cx: fretX(12), cy: y, r: 5, fill: "#8a6a4a" }));
  }
  for (let fret = 0; fret <= FRETS; fret++) {
    const x = NUT_X + fret * FRET_W;
    svg.append(el("line", {
      x1: x, y1: TOP, x2: x, y2: bottom,
      stroke: fret === 0 ? "#d4d4d4" : "#9ca3af", "stroke-width": fret === 0 ? 5 : 2,
    }));
    if (fret) {
      svg.append(el("text", {
        x: fretX(fret), y: bottom + 22, "text-anchor": "middle", "dominant-baseline": "central", fill: MUTED, "font-size": 8,
      }, String(fret)));
    }
  }

  const shape = currentShape();
  state.strings.forEach((openNote, s) => {
    const y = TOP + s * STRING_GAP;
    svg.append(el("line", { x1: NUT_X, y1: y, x2: right, y2: y, stroke: "#d1d5db", "stroke-width": 1 + s * 0.4 }));
    if (shape) {
      // Only the shape: one dot per string, or a cross on a muted string
      const fret = shape[shape.length - 1 - s]; // shapes run low string first, the neck high string first
      if (fret === null) {
        svg.append(el("text", {
          x: NUT_X / 2, y, "text-anchor": "middle", "dominant-baseline": "central", fill: MUTED, "font-size": 11, "font-weight": "bold",
        }, "✕"));
        return;
      }
      if (fret) drawOpenString(svg, y, openNote);
      const note = mod(openNote + fret);
      drawDot(svg, fretX(fret), y, note, CHORD_COLOR, note === state.selectedChord[0]);
      return;
    }
    for (let fret = 0; fret <= FRETS; fret++) {
      const note = mod(openNote + fret);
      const { fill, isRoot } = noteStyle(note);
      if (fill) drawDot(svg, fretX(fret), y, note, fill, isRoot);
      else if (fret === 0) drawOpenString(svg, y, note);
    }
  });
}

function drawDot(svg, x, y, note, fill, isRoot) {
  svg.append(el("circle", {
    cx: x, cy: y, r: 10, fill, stroke: isRoot ? ROOT_COLOR : "none", "stroke-width": 3,
  }));
  svg.append(el("text", {
    x, y, "text-anchor": "middle", "dominant-baseline": "central", "font-size": 7, "font-weight": "bold", fill: TEXT_ON[fill],
  }, nameOf(note)));
}

// A grey name left of the nut, so the tuning is always visible
function drawOpenString(svg, y, note) {
  svg.append(el("circle", { cx: NUT_X / 2, cy: y, r: 10, fill: PANEL, stroke: BORDER }));
  svg.append(el("text", {
    x: NUT_X / 2, y, "text-anchor": "middle", "dominant-baseline": "central", "font-size": 7, fill: MUTED,
  }, nameOf(note)));
}

// --- Click handling ---

function svgPoint(svg, event) {
  const point = svg.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  return point.matrixTransform(svg.getScreenCTM().inverse());
}

function onGuitarClick(event) {
  const point = svgPoint($("guitar"), event);
  const s = Math.round((point.y - TOP) / STRING_GAP);
  if (s < 0 || s >= state.strings.length) return;
  const fret = point.x < NUT_X ? 0 : Math.floor((point.x - NUT_X) / FRET_W) + 1;
  if (fret > FRETS) return;
  press(mod(state.strings[s] + fret), state.stringPitches[s] + fret);
}

function onPianoClick(event) {
  const key = event.target.closest("[data-pitch]");
  if (key) press(Number(key.dataset.note), Number(key.dataset.pitch));
}

// --- Start up ---

async function start() {
  setStrings(parseTuning(TUNINGS["Standard"]));
  $("tuning").value = tuningLabel("Standard");
  $("tuning-preset").replaceChildren(
    ...Object.keys(TUNINGS).map(name => new Option(tuningLabel(name), name)),
    new Option("Custom", ""),
  );
  $("tuning-preset").value = "Standard";

  midiOutputList = await midiOutputs();
  const output = $("output");
  output.replaceChildren(new Option(BUILT_IN_SYNTH), ...[...midiOutputList.keys()].map(name => new Option(name)));
  output.value = midiOutputList.has(WINDOWS_SYNTH) ? WINDOWS_SYNTH : BUILT_IN_SYNTH;
  $("instrument").replaceChildren(...[...INSTRUMENTS.keys()].map(name => new Option(name)));
  $("instrument").value = "Acoustic Grand Piano";
  $("family").replaceChildren(new Option(ALL_SCALES), ...[...SCALE_FAMILIES.keys()].map(name => new Option(name)));
  setOutput(false);

  renderResults();
  drawVisuals();
}

$("analyze").addEventListener("click", analyze);
$("clear").addEventListener("click", clear);
$("play-notes").addEventListener("click", playNotes);
$("play-scale").addEventListener("click", playScale);
$("notes").addEventListener("keydown", event => {
  if (event.key === "Enter") analyze();
});
$("output").addEventListener("change", () => setOutput());
$("instrument").addEventListener("change", setInstrument);
$("tuning-preset").addEventListener("change", () => {
  if ($("tuning-preset").value) {
    $("tuning").value = tuningLabel($("tuning-preset").value); // the name lets setTuning spot Bass
    setTuning();
  }
});
$("tuning").addEventListener("change", setTuning);
$("tuning").addEventListener("keydown", event => {
  if (event.key === "Enter") setTuning();
});
$("previous-shape").addEventListener("click", () => stepShape(-1));
$("next-shape").addEventListener("click", () => stepShape(1));
$("play-shape").addEventListener("click", playShape);
$("family").addEventListener("change", fillScaleList);
$("scale-list").addEventListener("change", showScale);
$("piano").addEventListener("click", onPianoClick);
$("guitar").addEventListener("click", onGuitarClick);

start();
