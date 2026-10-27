import tkinter as tk
from tkinter import ttk

from music_helper import (
    NOTE_NAMES,
    PROGRESSIONS,
    SCALES,
    find_chords,
    find_scales,
    parse_notes,
    scale_chords,
)

# Highlight colours: your notes, other notes of the selected scale, scale root marker
NOTE_COLOR = "#3b82f6"
SCALE_COLOR = "#86efac"
ROOT_COLOR = "#f97316"

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


class MusicHelperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Music Helper")
        self.minsize(760, 760)
        self.notes = set()
        self.scales = []
        self.selected_scale = None  # (root, name)
        self.strings = self.parse_tuning(TUNINGS["Standard"])

        main = ttk.Frame(self, padding=12)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(5, weight=1)

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

        self.error_var = tk.StringVar()
        ttk.Label(main, textvariable=self.error_var, foreground="red").grid(row=1, column=0, columnspan=2, sticky="w", pady=4)

        self.piano = tk.Canvas(main, width=WHITE_W * 7 * OCTAVES + 1, height=WHITE_H + 1, highlightthickness=0, cursor="hand2")
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
                  foreground="#666").pack(side="left", padx=(8, 0))
        self.tuning_error_var = tk.StringVar()
        ttk.Label(guitar_frame, textvariable=self.tuning_error_var, foreground="red").pack(anchor="w")

        self.guitar = tk.Canvas(guitar_frame, width=NUT_X + FRET_W * FRETS + 10, highlightthickness=0, cursor="hand2")
        self.guitar.pack()
        self.guitar.bind("<Button-1>", self.on_guitar_click)

        legend = ttk.Frame(main)
        legend.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        for color, text in [(NOTE_COLOR, "Your notes"), (SCALE_COLOR, "Selected scale"), (ROOT_COLOR, "Scale root")]:
            swatch = tk.Canvas(legend, width=14, height=14, highlightthickness=0)
            swatch.create_oval(2, 2, 12, 12, fill=color, outline="")
            swatch.pack(side="left", padx=(10, 4))
            ttk.Label(legend, text=text).pack(side="left")

        # Left: chords and scales found for the notes
        left = ttk.Frame(main)
        left.grid(row=5, column=0, sticky="nsew", padx=(0, 6))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(5, weight=1)

        ttk.Label(left, text="Chords that match exactly", font=("", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.exact_var = tk.StringVar(value="-")
        ttk.Label(left, textvariable=self.exact_var, wraplength=340).grid(row=1, column=0, sticky="w", pady=(0, 8))

        ttk.Label(left, text="Chords hiding inside your notes", font=("", 10, "bold")).grid(row=2, column=0, sticky="w")
        self.inside_var = tk.StringVar(value="-")
        ttk.Label(left, textvariable=self.inside_var, wraplength=340).grid(row=3, column=0, sticky="w", pady=(0, 8))

        ttk.Label(left, text="Scales/modes containing your notes", font=("", 10, "bold")).grid(row=4, column=0, sticky="w")
        self.scale_list = tk.Listbox(left, exportselection=False, activestyle="none", height=8)
        self.scale_list.grid(row=5, column=0, sticky="nsew")
        self.scale_list.bind("<<ListboxSelect>>", lambda e: self.show_scale())
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.scale_list.yview)
        scroll.grid(row=5, column=1, sticky="ns")
        self.scale_list.config(yscrollcommand=scroll.set)

        # Right: chords and progressions for the selected scale
        right = ttk.Frame(main)
        right.grid(row=5, column=1, sticky="nsew", padx=(6, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self.scale_title_var = tk.StringVar(value="Pick a scale to see its chords")
        ttk.Label(right, textvariable=self.scale_title_var, font=("", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.details = tk.Text(right, wrap="word", state="disabled", height=8)
        self.details.grid(row=1, column=0, sticky="nsew")

        self.draw_visuals()

    # --- Note input ---

    def toggle_note(self, note):
        try:
            notes = parse_notes(self.notes_var.get())
        except ValueError:
            notes = set()
        notes ^= {note}
        self.notes_var.set(" ".join(NOTE_NAMES[n] for n in sorted(notes)))
        self.analyze()

    def clear(self):
        self.notes_var.set("")
        self.error_var.set("")
        self.exact_var.set("-")
        self.inside_var.set("-")
        self.notes = set()
        self.scales = []
        self.selected_scale = None
        self.scale_list.delete(0, "end")
        self.show_details("Pick a scale to see its chords", "")
        self.draw_visuals()

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

        exact, fits_inside = find_chords(self.notes)
        self.exact_var.set(", ".join(exact) or "none")
        self.inside_var.set(", ".join(fits_inside) or "none")

        self.scales = find_scales(self.notes)
        self.scale_list.delete(0, "end")
        for root, name in self.scales:
            self.scale_list.insert("end", f"{NOTE_NAMES[root]} {name}")

        if self.scales:
            self.scale_list.selection_set(0)
            self.show_scale()
        else:
            self.selected_scale = None
            self.show_details("No scale or mode contains all of those notes.", "")
            self.draw_visuals()

    def show_scale(self):
        selection = self.scale_list.curselection()
        if not selection:
            return
        root, name = self.scales[selection[0]]
        self.selected_scale = (root, name)
        chords = scale_chords(root, name)

        lines = [f"{degree}: {chord}" for degree, chord in enumerate(chords, start=1)]
        lines.append("\nProgression ideas:")
        for prog in PROGRESSIONS:
            lines.append(" -> ".join(chords[d - 1] for d in prog))
        self.show_details(f"Chords in {NOTE_NAMES[root]} {name}", "\n".join(lines))
        self.draw_visuals()

    def show_details(self, title, body):
        self.scale_title_var.set(title)
        self.details.config(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", body)
        self.details.config(state="disabled")

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
        for name in TUNINGS:
            if text in (name, self.tuning_label(name)):
                text = TUNINGS[name]
        try:
            self.strings = self.parse_tuning(text)
        except ValueError as error:
            self.tuning_error_var.set(str(error))
            return
        self.tuning_error_var.set("")
        self.draw_guitar()

    # --- Drawing ---

    def note_style(self, note):
        """Return (fill colour or None, is scale root) for a note."""
        scale_notes, root = set(), None
        if self.selected_scale:
            root, name = self.selected_scale
            scale_notes = {(root + s) % 12 for s in SCALES[name]}
        if note in self.notes:
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
            key = c.create_rectangle(x, 0, x + WHITE_W, WHITE_H, fill=fill or "white", outline="#333")
            label = c.create_text(x + WHITE_W / 2, WHITE_H - 14, text=NOTE_NAMES[note],
                                  fill="white" if fill == NOTE_COLOR else "#555", font=("", 9, "bold" if fill else "normal"))
            items = [key, label]
            if is_root:
                items.append(c.create_oval(x + WHITE_W / 2 - 5, WHITE_H - 40, x + WHITE_W / 2 + 5, WHITE_H - 30, fill=ROOT_COLOR, outline=""))
            for item in items:
                c.tag_bind(item, "<Button-1>", lambda e, n=note: self.toggle_note(n))

        for i in range(7 * OCTAVES):
            if i % 7 not in BLACK_AFTER:
                continue
            note = BLACK_AFTER[i % 7]
            x = (i + 1) * WHITE_W - BLACK_W / 2
            fill, is_root = self.note_style(note)
            key = c.create_rectangle(x, 0, x + BLACK_W, BLACK_H, fill=fill or "#222", outline="#111")
            items = [key]
            if fill:
                items.append(c.create_text(x + BLACK_W / 2, BLACK_H - 12, text=NOTE_NAMES[note],
                                           fill="white" if fill == NOTE_COLOR else "#14532d", font=("", 7, "bold")))
            if is_root:
                items.append(c.create_oval(x + BLACK_W / 2 - 4, BLACK_H - 34, x + BLACK_W / 2 + 4, BLACK_H - 26, fill=ROOT_COLOR, outline=""))
            for item in items:
                c.tag_bind(item, "<Button-1>", lambda e, n=note: self.toggle_note(n))

    def fret_x(self, fret):
        """Centre x of a fret position; fret 0 (open string) sits left of the nut."""
        return NUT_X / 2 if fret == 0 else NUT_X + (fret - 0.5) * FRET_W

    def draw_guitar(self):
        c = self.guitar
        c.delete("all")
        bottom = TOP + STRING_GAP * (len(self.strings) - 1)
        c.config(height=bottom + 40)
        right = NUT_X + FRET_W * FRETS
        c.create_rectangle(NUT_X, TOP, right, bottom, fill="#d6b48a", outline="")

        mid = (TOP + bottom) / 2
        for fret in FRET_MARKERS:
            x = self.fret_x(fret)
            c.create_oval(x - 5, mid - 5, x + 5, mid + 5, fill="#a07c50", outline="")
        x = self.fret_x(12)
        for y in (TOP + STRING_GAP * 1.5, bottom - STRING_GAP * 1.5):
            c.create_oval(x - 5, y - 5, x + 5, y + 5, fill="#a07c50", outline="")

        for fret in range(FRETS + 1):
            x = NUT_X + fret * FRET_W
            c.create_line(x, TOP, x, bottom, fill="#333" if fret == 0 else "#999", width=5 if fret == 0 else 2)
            if fret:
                c.create_text(self.fret_x(fret), bottom + 22, text=str(fret), fill="#666", font=("", 8))

        for s, open_note in enumerate(self.strings):
            y = TOP + s * STRING_GAP
            c.create_line(NUT_X, y, right, y, fill="#555", width=1 + s * 0.4)
            for fret in range(FRETS + 1):
                note = (open_note + fret) % 12
                fill, is_root = self.note_style(note)
                if not fill:
                    if fret == 0:  # always show the open string's name so the tuning is visible
                        c.create_oval(NUT_X / 2 - 10, y - 10, NUT_X / 2 + 10, y + 10, fill="white", outline="#bbb")
                        c.create_text(NUT_X / 2, y, text=NOTE_NAMES[note], font=("", 7), fill="#666")
                    continue
                x = self.fret_x(fret)
                c.create_oval(x - 10, y - 10, x + 10, y + 10, fill=fill,
                              outline=ROOT_COLOR if is_root else "", width=3)
                c.create_text(x, y, text=NOTE_NAMES[note], font=("", 7, "bold"),
                              fill="white" if fill == NOTE_COLOR else "#14532d")

    def on_guitar_click(self, event):
        s = round((event.y - TOP) / STRING_GAP)
        if not 0 <= s < len(self.strings):
            return
        fret = 0 if event.x < NUT_X else int((event.x - NUT_X) // FRET_W) + 1
        if fret > FRETS:
            return
        self.toggle_note((self.strings[s] + fret) % 12)


if __name__ == "__main__":
    MusicHelperApp().mainloop()
