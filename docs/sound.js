// Sound output: a built-in synth made with the Web Audio API, or any MIDI output the browser can see
// (on Windows that includes the General MIDI synth). Events are [start seconds, MIDI pitch, length seconds].
import { mod } from "./theory.js";

// General MIDI instruments to choose from, with their program numbers
export const INSTRUMENTS = new Map([
  ["Acoustic Grand Piano", 0],
  ["Bright Piano", 1],
  ["Electric Piano", 4],
  ["Harpsichord", 6],
  ["Vibraphone", 11],
  ["Drawbar Organ", 16],
  ["Church Organ", 19],
  ["Accordion", 21],
  ["Nylon Guitar", 24],
  ["Steel Guitar", 25],
  ["Clean Electric Guitar", 27],
  ["Overdriven Guitar", 29],
  ["Distortion Guitar", 30],
  ["Acoustic Bass", 32],
  ["Electric Bass", 33],
  ["Violin", 40],
  ["Harp", 46],
  ["Strings", 48],
  ["Choir", 52],
  ["Trumpet", 56],
  ["Brass Section", 61],
  ["Alto Sax", 65],
  ["Flute", 73],
  ["New Age Pad", 88],
  ["Warm Pad", 89],
]);

// (harmonic, loudness) pairs give a soft, piano-like tone
const HARMONICS = [[1, 1.0], [2, 0.45], [3, 0.2], [4, 0.1]];
const DECAY = 3; // the sound fades as exp(-3t), as in sound.py
const ATTACK = 0.005; // seconds to reach full volume
const FADE = 0.03; // seconds of fade-out at the end of each note, so it doesn't click
const CONTROL_RATE = 2000; // points per second in the volume curve
const LEAD_IN = 0.05; // seconds between asking for a sound and hearing it

export function frequency(midi) {
  return 440 * 2 ** ((midi - 69) / 12);
}

// Turn note numbers 0-11 into rising MIDI pitches, the first at or above `start` (60 = middle C)
export function voice(notes, start = 60) {
  const pitches = [];
  for (const note of notes) {
    let pitch = start + mod(note - start);
    while (pitches.length && pitch <= pitches[pitches.length - 1]) pitch += 12;
    pitches.push(pitch);
  }
  return pitches;
}

const envelopes = new Map();
// The volume of one note over time, sampled as a curve for the Web Audio API
function envelope(length) {
  if (!envelopes.has(length)) {
    const points = Math.max(2, Math.round(length * CONTROL_RATE));
    const curve = new Float32Array(points);
    for (let k = 0; k < points; k++) {
      const t = (k / (points - 1)) * length;
      let value = Math.min(1, t / ATTACK) * Math.exp(-DECAY * t);
      if (t > length - FADE) value *= Math.max(0, (length - t) / FADE);
      curve[k] = value;
    }
    envelopes.set(length, curve);
  }
  return envelopes.get(length);
}

// Plays through the browser's audio; starting a new sound cuts off the previous one.
export class SynthPlayer {
  constructor() {
    this.context = null;
    this.generation = 0; // changes whenever a sound starts or stops
    this.startTime = 0; // when the current sound begins, in this player's clock (see now)
    this.current = null;
  }

  now() {
    return this.context ? this.context.currentTime : 0;
  }

  setProgram() {
    // The built-in synth has a single sound
  }

  stop() {
    this.generation += 1;
    const sound = this.current;
    this.current = null;
    if (!sound) return;
    const { context, master, oscillators } = sound;
    const now = context.currentTime;
    master.gain.cancelScheduledValues(now);
    master.gain.setValueAtTime(master.gain.value, now);
    master.gain.linearRampToValueAtTime(0, now + 0.03);
    for (const oscillator of oscillators) oscillator.stop(now + 0.04);
    setTimeout(() => master.disconnect(), 100);
  }

  play(events) {
    if (!events.length) return null;
    this.stop();
    if (!this.context) this.context = new AudioContext();
    const context = this.context;
    if (context.state === "suspended") context.resume();
    const generation = this.generation;
    const start = context.currentTime + LEAD_IN;

    const master = context.createGain();
    master.gain.value = 0.25;
    const compressor = context.createDynamicsCompressor(); // keeps big chords from clipping
    master.connect(compressor).connect(context.destination);

    const oscillators = [];
    for (const [offset, midi, length] of events) {
      const when = start + offset;
      const note = context.createGain();
      note.gain.setValueCurveAtTime(envelope(length), when, length);
      note.connect(master);
      for (const [harmonic, loudness] of HARMONICS) {
        const oscillator = context.createOscillator();
        oscillator.frequency.value = frequency(midi) * harmonic;
        const level = context.createGain();
        level.gain.value = loudness;
        oscillator.connect(level).connect(note);
        oscillator.start(when);
        oscillator.stop(when + length);
        oscillators.push(oscillator);
      }
    }
    this.current = { context, master, oscillators };
    this.startTime = start;
    return generation;
  }
}

// Plays through a MIDI output, with the chosen General MIDI instrument
export class MidiPlayer {
  constructor(output, program = 0) {
    this.output = output;
    this.generation = 0;
    this.startTime = 0;
    this.setProgram(program);
  }

  now() {
    return performance.now() / 1000;
  }

  setProgram(program) {
    this.output.send([0xc0, program]);
  }

  notesOff() {
    this.output.send([0xb0, 120, 0]); // all sound off
    this.output.send([0xb0, 123, 0]); // all notes off
  }

  stop() {
    this.generation += 1;
    this.output.clear?.(); // drop anything already scheduled
    this.notesOff();
  }

  play(events) {
    if (!events.length) return null;
    this.stop();
    const generation = this.generation;
    const start = this.now() + LEAD_IN;
    // Note-offs sort before note-ons at the same moment, so a repeated note sounds again
    const messages = [
      ...events.map(([offset, pitch]) => [offset, 1, [0x90, pitch, 100]]),
      ...events.map(([offset, pitch, length]) => [offset + length, 0, [0x80, pitch, 0]]),
    ].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    for (const [at, , bytes] of messages) {
      this.output.send(bytes, (start + at) * 1000); // Web MIDI times are in milliseconds on this clock
    }
    this.startTime = start;
    return generation;
  }
}

// The MIDI outputs the browser can see, as a Map of name -> output. Empty where Web MIDI isn't available.
export async function midiOutputs() {
  const outputs = new Map();
  if (!navigator.requestMIDIAccess) return outputs;
  try {
    const access = await navigator.requestMIDIAccess();
    for (const output of access.outputs.values()) outputs.set(output.name, output);
  } catch {
    // MIDI was blocked or isn't available, so only the built-in synth is offered
  }
  return outputs;
}
