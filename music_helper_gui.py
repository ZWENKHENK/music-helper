import ctypes
import tkinter as tk
from tkinter import ttk

from music_helper import (
    NOTE_NAMES,
    PROGRESSIONS,
    SCALE_FAMILIES,
    SCALES,
    chord_notes,
    find_chords,
    find_scales,
    fitting_chords,
    parse_notes,
    scale_chords,
    guitar_shapes,
    shape_text,
    spell_scale,
)
from sound import Player, voice

# Dark theme colours
BG = "#1e1f22"
PANEL = "#2b2d31"
HOVER = "#383a40"
BORDER = "#3f4248"
FG = "#e3e5e8"
MUTED = "#949ba4"
ERROR = "#f87171"
LINK = "#93c5fd"

# Highlight colours, and the text colour that reads well on each
NOTE_COLOR = "#3b82f6"
SCALE_COLOR = "#86efac"
CHORD_COLOR = "#c084fc"
ROOT_COLOR = "#f97316"
TEXT_ON = {NOTE_COLOR: "white", SCALE_COLOR: "#14532d", CHORD_COLOR: "#2e1065"}

# Piano layout: semitones of the white keys, and which white key each black key follows
WHITE_STEPS = [0, 2, 4, 5, 7, 9, 11]
BLACK_AFTER = {0: 1, 1: 3, 3: 6, 4: 8, 5: 10}  # white index in octave -> black note
OCTAVES = 2
WHITE_W, WHITE_H = 36, 130
BLACK_W, BLACK_H = 22, 80

# Guitar tunings, written low string to high; the neck draws the high string at the top like tab
TUNINGS = {
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
}
MIN_STRINGS, MAX_STRINGS = 4, 8
FRETS = 12
NUT_X, FRET_W, STRING_GAP, TOP = 44, 52, 26, 18
FRET_MARKERS = [3, 5, 7, 9]

CHORD_HINT = "Click a chord name to show it on the piano and guitar."
ALL_SCALES = "All scales"
PIANO_START = 60  # the piano's lowest C is middle C
LOWEST_STRING = 40  # E2, a guitar's low E; other tunings put their lowest string as near to this as possible
CHORD_LENGTH, SCALE_STEP, PROGRESSION_STEP = 1.6, 0.3, 0.9  # seconds


def chord_tag(chord):
    return f"chord:{chord[0]}:{chord[1]}"


class MusicHelperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Music Helper")
        self.minsize(760, 800)
        self.notes = set()
        self.exact, self.fits_inside = [], []
        self.all_scales = []  # every scale containing the notes
        self.scales = []  # the ones shown, after the family filter
        self.selected_scale = None  # (root, name)
        self.selected_chord = None  # (root, quality)
        self.spelling = {}  # note number -> name, from the selected scale
        self.set_strings(self.parse_tuning(TUNINGS["Standard"]))
        self.shapes = []  # guitar shapes for the selected chord, low string first
        self.shape_index = None  # which shape is on the neck; None shows every position
        self.shapes_key = None  # (chord, tuning) the shapes were found for
        self.player = Player()
        self.play_on_click = tk.BooleanVar(value=True)
        self.setup_theme()

        main = ttk.Frame(self, padding=12)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(6, weight=1)

        # Note input: type them, or click the piano / guitar
        entry_row = ttk.Frame(main)
        entry_row.grid(row=0, column=0, columnspan=2, sticky="ew")
        entry_row.columnconfigure(1, weight=1)
        ttk.Label(entry_row, text="Notes:").grid(row=0, column=0, padx=(0, 6))
        self.notes_var = tk.StringVar()
        entry = ttk.Entry(entry_row, textvariable=self.notes_var)
        entry.grid(row=0, column=1, sticky="ew")
        entry.bind("<Return>", lambda e: self.analyze())
        entry.focus()
        ttk.Button(entry_row, text="Analyze", command=self.analyze).grid(row=0, column=2, padx=(6, 0))
        ttk.Button(entry_row, text="Clear", command=self.clear).grid(row=0, column=3, padx=(6, 0))
        ttk.Button(entry_row, text="▶ Play", command=self.play_notes).grid(row=0, column=4, padx=(6, 0))
        ttk.Checkbutton(entry_row, text="Play on click", variable=self.play_on_click).grid(row=0, column=5, padx=(10, 0))

        self.error_var = tk.StringVar()
        ttk.Label(main, textvariable=self.error_var, foreground=ERROR).grid(row=1, column=0, columnspan=2, sticky="w", pady=4)

        self.piano = tk.Canvas(main, width=WHITE_W * 7 * OCTAVES + 1, height=WHITE_H + 1, bg=BG, highlightthickness=0, cursor="hand2")
        self.piano.grid(row=2, column=0, columnspan=2, pady=(0, 10))

        guitar_frame = ttk.Frame(main)
        guitar_frame.grid(row=3, column=0, columnspan=2, pady=(0, 6))
        tuning_row = ttk.Frame(guitar_frame)
        tuning_row.pack(anchor="w", pady=(0, 4))
        ttk.Label(tuning_row, text="Tuning:").pack(side="left", padx=(0, 6))
        self.tuning_var = tk.StringVar(value=self.tuning_label("Standard"))
        tuning_box = ttk.Combobox(tuning_row, textvariable=self.tuning_var, width=32,
                                  values=[self.tuning_label(name) for name in TUNINGS])
        tuning_box.pack(side="left")
        tuning_box.bind("<<ComboboxSelected>>", lambda e: self.set_tuning())
        tuning_box.bind("<Return>", lambda e: self.set_tuning())
        ttk.Label(tuning_row, text="or type your own, low to high, and press Enter",
                  foreground=MUTED).pack(side="left", padx=(8, 0))
        shape_row = ttk.Frame(guitar_frame)
        shape_row.pack(anchor="w", pady=(0, 4))
        ttk.Label(shape_row, text="Chord shape:").pack(side="left", padx=(0, 6))
        previous_shape = ttk.Button(shape_row, text="‹", width=3, command=lambda: self.step_shape(-1))
        previous_shape.pack(side="left")
        self.shape_var = tk.StringVar()
        ttk.Label(shape_row, textvariable=self.shape_var, width=40, anchor="center").pack(side="left", padx=6)
        next_shape = ttk.Button(shape_row, text="›", width=3, command=lambda: self.step_shape(1))
        next_shape.pack(side="left")
        play_shape = ttk.Button(shape_row, text="▶ Play shape", command=self.play_shape)
        play_shape.pack(side="left", padx=(6, 0))
        self.shape_buttons = [previous_shape, next_shape, play_shape]

        self.tuning_error_var = tk.StringVar()
        ttk.Label(tuning_row, textvariable=self.tuning_error_var, foreground=ERROR).pack(side="left", padx=(8, 0))

        self.guitar = tk.Canvas(guitar_frame, width=NUT_X + FRET_W * FRETS + 10, bg=BG, highlightthickness=0, cursor="hand2")
        self.guitar.pack()
        self.guitar.bind("<Button-1>", self.on_guitar_click)

        legend = ttk.Frame(main)
        legend.grid(row=4, column=0, columnspan=2)
        for color, text in [(NOTE_COLOR, "Your notes"), (SCALE_COLOR, "Selected scale"),
                            (CHORD_COLOR, "Selected chord"), (ROOT_COLOR, "Root")]:
            swatch = tk.Canvas(legend, width=14, height=14, bg=BG, highlightthickness=0)
            swatch.create_oval(2, 2, 12, 12, fill=color, outline="")
            swatch.pack(side="left", padx=(10, 4))
            ttk.Label(legend, text=text).pack(side="left")

        self.chord_status_var = tk.StringVar(value=CHORD_HINT)
        ttk.Label(main, textvariable=self.chord_status_var, foreground=MUTED).grid(row=5, column=0, columnspan=2, pady=(4, 10))

        # Left: chords and scales found for the notes
        left = ttk.Frame(main)
        left.grid(row=6, column=0, sticky="nsew", padx=(0, 6))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(6, weight=1)

        ttk.Label(left, text="Chords that match exactly", style="Heading.TLabel").grid(row=0, column=0, sticky="w")
        self.exact_text = self.make_text(left, height=2, bg=BG)
        self.exact_text.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        ttk.Label(left, text="Chords hiding inside your notes", style="Heading.TLabel").grid(row=2, column=0, sticky="w")
        self.inside_text = self.make_text(left, height=3, bg=BG)
        self.inside_text.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        self.scales_heading_var = tk.StringVar(value="Scales containing your notes")
        ttk.Label(left, textvariable=self.scales_heading_var, style="Heading.TLabel").grid(row=4, column=0, sticky="w")
        filter_row = ttk.Frame(left)
        filter_row.grid(row=5, column=0, columnspan=2, sticky="w", pady=(2, 4))
        ttk.Label(filter_row, text="Show:").pack(side="left", padx=(0, 6))
        self.family_var = tk.StringVar(value=ALL_SCALES)
        family_box = ttk.Combobox(filter_row, textvariable=self.family_var, state="readonly", width=24,
                                  values=[ALL_SCALES, *SCALE_FAMILIES])
        family_box.pack(side="left")
        family_box.bind("<<ComboboxSelected>>", lambda e: self.fill_scale_list())
        self.scale_list = tk.Listbox(left, exportselection=False, activestyle="none", height=8,
                                     bg=PANEL, fg=FG, selectbackground=NOTE_COLOR, selectforeground="white",
                                     relief="flat", highlightthickness=1, highlightbackground=BORDER, highlightcolor=BORDER)
        self.scale_list.grid(row=6, column=0, sticky="nsew")
        self.scale_list.bind("<<ListboxSelect>>", lambda e: self.show_scale())
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.scale_list.yview)
        scroll.grid(row=6, column=1, sticky="ns")
        self.scale_list.config(yscrollcommand=scroll.set)

        # Right: chords and progressions for the selected scale
        right = ttk.Frame(main)
        right.grid(row=6, column=1, sticky="nsew", padx=(6, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self.scale_title_var = tk.StringVar(value="Pick a scale to see its chords")
        ttk.Label(right, textvariable=self.scale_title_var, style="Heading.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(right, text="▶ Play scale", command=self.play_scale).grid(row=0, column=1, sticky="e", pady=(0, 4))
        self.details = self.make_text(right, height=8, bg=PANEL, padx=8, pady=6,
                                      highlightthickness=1, highlightbackground=BORDER, highlightcolor=BORDER)
        self.details.grid(row=1, column=0, columnspan=2, sticky="nsew")

        self.chord_texts = [self.exact_text, self.inside_text, self.details]
        self.render_results()
        self.draw_visuals()
        self.use_dark_title_bar()

    # --- Theme ---

    def setup_theme(self):
        self.configure(bg=BG)
        style = ttk.Style(self)
        style.theme_use("clam")  # the native Windows theme ignores most colour settings
        style.configure(".", background=BG, foreground=FG, bordercolor=BORDER, focuscolor=BG,
                        troughcolor=BG, selectbackground=NOTE_COLOR, selectforeground="white")
        style.configure("Heading.TLabel", font=("", 10, "bold"))
        style.configure("TButton", background=PANEL, lightcolor=PANEL, darkcolor=PANEL, padding=(10, 3))
        style.map("TButton", background=[("pressed", BORDER), ("active", HOVER)], foreground=[("disabled", MUTED)])
        for widget in ("TEntry", "TCombobox"):
            style.configure(widget, fieldbackground=PANEL, background=PANEL, insertcolor=FG,
                            lightcolor=PANEL, darkcolor=PANEL, arrowcolor=FG)
            style.map(widget, bordercolor=[("focus", NOTE_COLOR)], fieldbackground=[("readonly", PANEL)],
                      background=[("active", HOVER)], lightcolor=[("focus", PANEL)])
        style.configure("TCheckbutton", indicatorbackground=PANEL, indicatorforeground="white", upperbordercolor=BORDER, lowerbordercolor=BORDER)
        style.map("TCheckbutton", background=[("active", BG)], indicatorbackground=[("selected", NOTE_COLOR)])
        style.configure("Vertical.TScrollbar", background=PANEL, lightcolor=PANEL, darkcolor=PANEL, arrowcolor=MUTED)
        style.map("Vertical.TScrollbar", background=[("active", HOVER)])
        # The combobox dropdown is a plain Tk listbox, styled through the option database
        self.option_add("*TCombobox*Listbox.background", PANEL)
        self.option_add("*TCombobox*Listbox.foreground", FG)
        self.option_add("*TCombobox*Listbox.selectBackground", NOTE_COLOR)
        self.option_add("*TCombobox*Listbox.selectForeground", "white")

    def use_dark_title_bar(self):
        """Ask Windows 10/11 for a dark title bar; harmless no-op elsewhere."""
        try:
            self.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            dark = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark), ctypes.sizeof(dark))
        except (AttributeError, OSError):
            pass

    # --- Note input ---

    def name(self, note):
        """Name a note using the selected scale's spelling, falling back to sharps."""
        return self.spelling.get(note, NOTE_NAMES[note])

    def chord_name(self, chord):
        root, quality = chord
        return f"{self.name(root)} {quality}"

    def press(self, note, pitch):
        """A piano key or fret was clicked: play it, and add or remove the note."""
        if self.play_on_click.get():
            self.player.play([(0, pitch, CHORD_LENGTH)])
        self.toggle_note(note)

    def toggle_note(self, note):
        try:
            notes = parse_notes(self.notes_var.get())
        except ValueError:
            notes = set()
        notes ^= {note}
        self.notes_var.set(" ".join(NOTE_NAMES[n] for n in sorted(notes)))
        self.analyze()
        # Respell with the scale that was just picked, e.g. "A# D F" becomes "Bb D F"
        self.notes_var.set(" ".join(self.name(n) for n in sorted(notes)))

    def clear(self):
        self.notes_var.set("")
        self.error_var.set("")
        self.notes = set()
        self.exact, self.fits_inside = [], []
        self.all_scales = []
        self.fill_scale_list()

    def analyze(self):
        text = self.notes_var.get()
        if not text.strip():
            self.clear()
            return
        try:
            self.notes = parse_notes(text)
        except ValueError as error:
            self.error_var.set(str(error))
            return
        self.error_var.set("")

        self.exact, self.fits_inside = find_chords(self.notes)
        self.all_scales = find_scales(self.notes)
        self.selected_scale = None  # so the first matching scale gets picked
        self.fill_scale_list()

    def fill_scale_list(self):
        """Show the matching scales in the chosen family, keeping the selected scale if it's still listed."""
        family = self.family_var.get()
        if family == ALL_SCALES:
            self.scales = self.all_scales
            count = f" ({len(self.scales)})"
        else:
            self.scales = [s for s in self.all_scales if s[1] in SCALE_FAMILIES[family]]
            count = f" ({len(self.scales)} of {len(self.all_scales)})"
        self.scales_heading_var.set("Scales containing your notes" + (count if self.notes else ""))
        self.scale_list.delete(0, "end")
        for root, name in self.scales:
            self.scale_list.insert("end", f"{spell_scale(root, name)[root]} {name}")

        if self.selected_scale in self.scales:
            index = self.scales.index(self.selected_scale)
            self.scale_list.selection_set(index)
            self.scale_list.see(index)
        elif self.scales:
            self.scale_list.selection_set(0)
            self.show_scale()
        else:
            self.selected_scale = None
            self.selected_chord = None
            self.spelling = {}
            self.render_results()
            self.draw_visuals()

    def show_scale(self):
        selection = self.scale_list.curselection()
        if not selection:
            return
        self.selected_scale = self.scales[selection[0]]
        self.selected_chord = None
        self.spelling = spell_scale(*self.selected_scale)
        self.render_results()
        self.draw_visuals()

    # --- Results text with clickable chords ---

    def make_text(self, parent, **options):
        text = tk.Text(parent, wrap="word", state="disabled", relief="flat", width=1, cursor="arrow",
                       font="TkDefaultFont", fg=FG, selectbackground=NOTE_COLOR, **options)
        text.tag_configure("heading", font=("", 10, "bold"))
        text.tag_configure("chord", foreground=LINK)
        text.tag_bind("chord", "<Enter>", lambda e: text.config(cursor="hand2"))
        text.tag_bind("chord", "<Leave>", lambda e: text.config(cursor="arrow"))
        return text

    def write_text(self, widget, parts):
        """Fill a read-only Text with parts: plain strings, ("heading", text), or (root, quality) chord links."""
        widget.config(state="normal")
        widget.delete("1.0", "end")
        for part in parts:
            if isinstance(part, str):
                widget.insert("end", part)
            elif part[0] == "heading":
                widget.insert("end", part[1], "heading")
            elif part[0] == "play":
                tag = f"play:{widget.index('end')}"
                widget.insert("end", "▶ ", ("chord", tag))
                widget.tag_bind(tag, "<Button-1>", lambda e, play=part[1]: play())
            else:
                tag = chord_tag(part)
                widget.insert("end", self.chord_name(part), ("chord", tag))
                widget.tag_bind(tag, "<Button-1>", lambda e, c=part: self.select_chord(c))
        widget.config(state="disabled")

    def chord_list(self, chords):
        if not chords:
            return ["none"]
        parts = []
        for chord in chords:
            parts += [chord, ", "]
        return parts[:-1]

    def render_results(self):
        self.write_text(self.exact_text, self.chord_list(self.exact) if self.notes else ["-"])
        self.write_text(self.inside_text, self.chord_list(self.fits_inside) if self.notes else ["-"])

        if not self.selected_scale:
            if self.all_scales:
                title = "No scale in this family contains all of those notes."
            elif self.notes:
                title = "No scale or mode contains all of those notes."
            else:
                title = "Pick a scale to see its chords"
            self.scale_title_var.set(title)
            self.write_text(self.details, [])
        else:
            root, name = self.selected_scale
            if len(SCALES[name]) != 7:
                self.scale_title_var.set(f"Chords that fit in {self.name(root)} {name}")
                parts = []
                for degree, chords in enumerate(fitting_chords(root, name), start=1):
                    parts.append(f"{degree}: ")
                    parts += self.chord_list(chords) if chords else ["-"]
                    parts.append("\n")
                self.write_text(self.details, parts)
                self.update_chord_highlight()
                return
            self.scale_title_var.set(f"Chords in {self.name(root)} {name}")
            chords = scale_chords(root, name)
            parts = []
            for degree, chord in enumerate(chords, start=1):
                parts += [f"{degree}: ", chord, "\n"]
            parts.append(("heading", "\nProgression ideas:\n"))
            for prog in PROGRESSIONS:
                parts.append(("play", lambda p=prog: self.play_progression([chords[d - 1] for d in p])))
                for i, d in enumerate(prog):
                    parts += [" -> " if i else "", chords[d - 1]]
                parts.append("\n")
            self.write_text(self.details, parts)
        self.update_chord_highlight()

    def select_chord(self, chord):
        self.selected_chord = None if chord == self.selected_chord else chord
        self.update_chord_highlight()
        self.draw_visuals()
        if self.selected_chord and self.play_on_click.get():
            self.play_shape()

    def update_chord_highlight(self):
        selected = chord_tag(self.selected_chord) if self.selected_chord else None
        for widget in self.chord_texts:
            for tag in widget.tag_names():
                if tag.startswith("chord:"):
                    on = tag == selected
                    widget.tag_configure(tag, background=CHORD_COLOR if on else "", foreground=TEXT_ON[CHORD_COLOR] if on else "")
        if self.selected_chord:
            names = " ".join(self.name(n) for n in chord_notes(*self.selected_chord))
            self.chord_status_var.set(f"Showing {self.chord_name(self.selected_chord)}: {names}. Click it again to hide.")
        else:
            self.chord_status_var.set(CHORD_HINT)
        self.update_shapes()

    # --- Guitar chord shapes ---

    def update_shapes(self):
        """Find shapes for the selected chord in the current tuning, starting again at the first one."""
        key = (self.selected_chord, tuple(self.strings))
        if key == self.shapes_key:
            return
        self.shapes_key = key
        self.shapes = guitar_shapes(self.strings[::-1], *self.selected_chord, frets=FRETS) if self.selected_chord else []
        self.shape_index = 0 if self.shapes else None
        self.update_shape_label()

    def current_shape(self):
        return None if self.shape_index is None else self.shapes[self.shape_index]

    def update_shape_label(self):
        if not self.selected_chord:
            text = "click a chord name to see guitar shapes"
        elif not self.shapes:
            text = f"no practical {self.chord_name(self.selected_chord)} shapes in this tuning"
        elif self.shape_index is None:
            text = f"{self.chord_name(self.selected_chord)}: every position"
        else:
            shape = shape_text(self.current_shape())
            text = f"{self.chord_name(self.selected_chord)}:  {shape}   ({self.shape_index + 1} of {len(self.shapes)})"
        self.shape_var.set(text)
        for button in self.shape_buttons:
            button.state(["!disabled"] if self.shapes else ["disabled"])

    def step_shape(self, step):
        """Move through the shapes, with 'every position' between the last and the first."""
        positions = [None, *range(len(self.shapes))]
        self.shape_index = positions[(positions.index(self.shape_index) + step) % len(positions)]
        self.update_shape_label()
        self.draw_guitar()
        if self.shape_index is not None and self.play_on_click.get():
            self.play_shape()

    def play_shape(self):
        """Strum the shape on the neck from the low string up, or play the chord if no shape is shown."""
        shape = self.current_shape()
        if not shape:
            if self.selected_chord:
                self.play_progression([self.selected_chord])
            return
        pitches = [p + f for p, f in zip(self.string_pitches[::-1], shape) if f is not None]
        self.player.play([(j * 0.04, p, CHORD_LENGTH) for j, p in enumerate(pitches)])

    # --- Playback ---

    def play_notes(self):
        """Play your notes one at a time, rising from middle C, then all together."""
        pitches = voice(sorted(self.notes))
        events = [(i * SCALE_STEP, p, SCALE_STEP * 1.5) for i, p in enumerate(pitches)]
        start = len(pitches) * SCALE_STEP
        self.player.play(events + [(start, p, CHORD_LENGTH) for p in pitches])

    def play_scale(self):
        if not self.selected_scale:
            return
        root, name = self.selected_scale
        pitches = voice([(root + s) % 12 for s in SCALES[name]] + [root])
        self.player.play([(i * SCALE_STEP, p, SCALE_STEP * 1.5) for i, p in enumerate(pitches)])

    def play_progression(self, chords):
        """Play chords one after another, each strummed slightly from the root up."""
        events = []
        for i, chord in enumerate(chords):
            for j, pitch in enumerate(voice(chord_notes(*chord))):
                events.append((i * PROGRESSION_STEP + j * 0.03, pitch, CHORD_LENGTH if i == len(chords) - 1 else PROGRESSION_STEP))
        self.player.play(events)

    # --- Guitar tuning ---

    @staticmethod
    def tuning_label(name):
        return f"{name} ({TUNINGS[name]})"

    @staticmethod
    def parse_tuning(text):
        """Turn 'E A D G B E' (low to high) into note numbers, high string first."""
        strings = [parse_notes(word).pop() for word in text.replace(",", " ").split()]
        if not MIN_STRINGS <= len(strings) <= MAX_STRINGS:
            raise ValueError(f"A tuning needs {MIN_STRINGS} to {MAX_STRINGS} strings")
        return strings[::-1]

    def set_tuning(self):
        text = self.tuning_var.get()
        lowest = LOWEST_STRING
        for name in TUNINGS:
            if text in (name, self.tuning_label(name)):
                text = TUNINGS[name]
                if name == "Bass":
                    lowest -= 12  # bass strings sound an octave below a guitar's
        try:
            self.set_strings(self.parse_tuning(text), lowest)
        except ValueError as error:
            self.tuning_error_var.set(str(error))
            return
        self.tuning_error_var.set("")
        self.update_shapes()
        self.draw_guitar()

    def set_strings(self, strings, lowest=LOWEST_STRING):
        """Store a tuning (high string first) and work out each open string's actual pitch.

        The lowest string is put as close as possible to the `lowest` pitch, and each string above it is higher.
        """
        self.strings = strings
        low_first = strings[::-1]
        lowest += (low_first[0] - lowest + 6) % 12 - 6
        self.string_pitches = voice(low_first, start=lowest)[::-1]

    # --- Drawing ---

    def note_style(self, note):
        """Return (fill colour or None, is root) for a note. A selected chord takes priority over the scale."""
        scale_notes, chord, root = set(), set(), None
        if self.selected_scale:
            root, name = self.selected_scale
            scale_notes = {(root + s) % 12 for s in SCALES[name]}
        if self.selected_chord:
            root = self.selected_chord[0]
            chord = set(chord_notes(*self.selected_chord))
        if note in chord:
            fill = CHORD_COLOR
        elif note in self.notes:
            fill = NOTE_COLOR
        elif note in scale_notes:
            fill = SCALE_COLOR
        else:
            fill = None
        return fill, note == root

    def draw_visuals(self):
        self.draw_piano()
        self.draw_guitar()

    def draw_piano(self):
        c = self.piano
        c.delete("all")
        for i in range(7 * OCTAVES):
            note = WHITE_STEPS[i % 7]
            x = i * WHITE_W
            fill, is_root = self.note_style(note)
            key = c.create_rectangle(x, 0, x + WHITE_W, WHITE_H, fill=fill or "#ececec", outline=BG)
            label = c.create_text(x + WHITE_W / 2, WHITE_H - 14, text=self.name(note),
                                  fill=TEXT_ON.get(fill, "#555"), font=("", 9, "bold" if fill else "normal"))
            items = [key, label]
            if is_root:
                items.append(c.create_oval(x + WHITE_W / 2 - 5, WHITE_H - 40, x + WHITE_W / 2 + 5, WHITE_H - 30, fill=ROOT_COLOR, outline=""))
            for item in items:
                c.tag_bind(item, "<Button-1>", lambda e, n=note, p=PIANO_START + 12 * (i // 7) + note: self.press(n, p))

        for i in range(7 * OCTAVES):
            if i % 7 not in BLACK_AFTER:
                continue
            note = BLACK_AFTER[i % 7]
            x = (i + 1) * WHITE_W - BLACK_W / 2
            fill, is_root = self.note_style(note)
            key = c.create_rectangle(x, 0, x + BLACK_W, BLACK_H, fill=fill or "#18181b", outline=BG)
            items = [key]
            if fill:
                items.append(c.create_text(x + BLACK_W / 2, BLACK_H - 12, text=self.name(note),
                                           fill=TEXT_ON[fill], font=("", 7, "bold")))
            if is_root:
                items.append(c.create_oval(x + BLACK_W / 2 - 4, BLACK_H - 34, x + BLACK_W / 2 + 4, BLACK_H - 26, fill=ROOT_COLOR, outline=""))
            for item in items:
                c.tag_bind(item, "<Button-1>", lambda e, n=note, p=PIANO_START + 12 * (i // 7) + note: self.press(n, p))

    def fret_x(self, fret):
        """Centre x of a fret position; fret 0 (open string) sits left of the nut."""
        return NUT_X / 2 if fret == 0 else NUT_X + (fret - 0.5) * FRET_W

    def draw_guitar(self):
        c = self.guitar
        c.delete("all")
        bottom = TOP + STRING_GAP * (len(self.strings) - 1)
        c.config(height=bottom + 40)
        right = NUT_X + FRET_W * FRETS
        c.create_rectangle(NUT_X, TOP, right, bottom, fill="#5c4330", outline="")

        mid = (TOP + bottom) / 2
        for fret in FRET_MARKERS:
            x = self.fret_x(fret)
            c.create_oval(x - 5, mid - 5, x + 5, mid + 5, fill="#8a6a4a", outline="")
        x = self.fret_x(12)
        for y in (TOP + STRING_GAP * 1.5, bottom - STRING_GAP * 1.5):
            c.create_oval(x - 5, y - 5, x + 5, y + 5, fill="#8a6a4a", outline="")

        for fret in range(FRETS + 1):
            x = NUT_X + fret * FRET_W
            c.create_line(x, TOP, x, bottom, fill="#d4d4d4" if fret == 0 else "#9ca3af", width=5 if fret == 0 else 2)
            if fret:
                c.create_text(self.fret_x(fret), bottom + 22, text=str(fret), fill=MUTED, font=("", 8))

        shape = self.current_shape()
        for s, open_note in enumerate(self.strings):
            y = TOP + s * STRING_GAP
            c.create_line(NUT_X, y, right, y, fill="#d1d5db", width=1 + s * 0.4)
            if shape:
                # Only the shape: one dot per string, or a cross on a muted string
                fret = shape[-1 - s]  # shapes run low string first, the neck high string first
                if fret is None:
                    c.create_text(NUT_X / 2, y, text="✕", fill=MUTED, font=("", 11, "bold"))
                    continue
                if fret:
                    self.draw_open_string(y, open_note)
                note = (open_note + fret) % 12
                self.draw_dot(self.fret_x(fret), y, note, CHORD_COLOR, note == self.selected_chord[0])
                continue
            for fret in range(FRETS + 1):
                note = (open_note + fret) % 12
                fill, is_root = self.note_style(note)
                if fill:
                    self.draw_dot(self.fret_x(fret), y, note, fill, is_root)
                elif fret == 0:
                    self.draw_open_string(y, note)

    def draw_dot(self, x, y, note, fill, is_root):
        self.guitar.create_oval(x - 10, y - 10, x + 10, y + 10, fill=fill, outline=ROOT_COLOR if is_root else "", width=3)
        self.guitar.create_text(x, y, text=self.name(note), font=("", 7, "bold"), fill=TEXT_ON[fill])

    def draw_open_string(self, y, note):
        """A grey name left of the nut, so the tuning is always visible."""
        self.guitar.create_oval(NUT_X / 2 - 10, y - 10, NUT_X / 2 + 10, y + 10, fill=PANEL, outline=BORDER)
        self.guitar.create_text(NUT_X / 2, y, text=self.name(note), font=("", 7), fill=MUTED)

    def on_guitar_click(self, event):
        s = round((event.y - TOP) / STRING_GAP)
        if not 0 <= s < len(self.strings):
            return
        fret = 0 if event.x < NUT_X else int((event.x - NUT_X) // FRET_W) + 1
        if fret > FRETS:
            return
        self.press((self.strings[s] + fret) % 12, self.string_pitches[s] + fret)


if __name__ == "__main__":
    MusicHelperApp().mainloop()
