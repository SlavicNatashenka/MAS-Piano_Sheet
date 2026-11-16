init 811 python:
    import store.mas_piano_keys as mas_piano_keys

    _PS_ASSET = "Submods/Piano Sheet/mod_assets/"

    class MASPianoSheetDisplayable(PianoDisplayable):
        # Sit to the right of Talk / Extra / Music / Noises / Play
        ZZPK_IMG_BACK_X = 200

        SHEET_W = 545
        SHEET_H = 96
        # Lyrics sit ~y=385 (50px tall). Keep the sheet under that bar.
        SHEET_GAP = 80
        WINDOW = 8
        TILE_W = 56
        TILE_H = 48
        TILE_GAP = 8

        _BLACK_NOTES = frozenset((
            mas_piano_keys.F4SH,
            mas_piano_keys.G4SH,
            mas_piano_keys.A4SH,
            mas_piano_keys.C5SH,
            mas_piano_keys.D5SH,
            mas_piano_keys.F5SH,
            mas_piano_keys.G5SH,
            mas_piano_keys.A5SH,
        ))

        def __init__(self, mode, pnml=None):
            super(MASPianoSheetDisplayable, self).__init__(mode, pnml=pnml)

            self._sheet_panel = Image(_PS_ASSET + "sheet_panel.png")
            self._tile_idle = Image(_PS_ASSET + "tile_idle.png")
            self._tile_current = Image(_PS_ASSET + "tile_current.png")
            self._tile_played = Image(_PS_ASSET + "tile_played.png")
            self._tile_sharp = Image(_PS_ASSET + "tile_sharp.png")
            self._tile_sharp_current = Image(_PS_ASSET + "tile_sharp_current.png")
            self._tile_sharp_played = Image(_PS_ASSET + "tile_sharp_played.png")
            self._tile_miss = Image(_PS_ASSET + "tile_miss.png")

        def _sheet_xy(self):
            """Sheet sits under Config / Quit, aligned with the piano."""
            x = self.ZZPK_IMG_BACK_X
            y = (
                self.ZZPK_IMG_BACK_Y
                + self.PIANO_BACK_HEIGHT
                + self.BUTTON_SPACING
                + self.BUTTON_HEIGHT
                + self.SHEET_GAP
            )
            return x, y

        def _physical_for_note(self, note):
            """Keyboard key the player actually presses for this piano note."""
            keymap = self.live_keymap or mas_piano_keys.KEYMAP
            for physical, mapped in keymap.items():
                if mapped == note:
                    return physical
            return note

        def _letter_for_note(self, note):
            """Display letter for a note, escaped for Ren'Py Text."""
            physical = self._physical_for_note(note)

            if physical in mas_piano_keys.NONCHAR_TEXT:
                return mas_piano_keys.NONCHAR_TEXT[physical]

            try:
                letter = chr(physical).upper()
            except Exception:
                return "?"

            if letter == "[":
                return "[["
            if letter == "{":
                return "{{"
            return letter

        def _sheet_sequence(self):
            """
            Current notes to guide, plus how far the player is.

            RETURNS:
                (notes, index, waiting)
                waiting True = free play, no song recognized yet
            """
            if self.state in self.CONFIG_STATES:
                return None, 0, False

            if self.match is None:
                return None, 0, True

            if self.state in self.POST_STATES:
                notes = self.match.postnotes or []
                return notes, self.match.matchdex, False

            notes = self.match.notes or []
            return notes, self.match.matchdex, False

        def _tile_for(self, note, status):
            """status: played, current, miss, idle"""
            sharp = note in self._BLACK_NOTES

            if status == "miss":
                return self._tile_miss
            if status == "played":
                return self._tile_sharp_played if sharp else self._tile_played
            if status == "current":
                return self._tile_sharp_current if sharp else self._tile_current
            return self._tile_sharp if sharp else self._tile_idle

        def _letter_color(self, note, status):
            sharp = note in self._BLACK_NOTES

            if status == "miss":
                return "#FFFFFF"
            if status == "played":
                return "#CDBFD6" if sharp else "#EDE4F0"
            if status == "current":
                return "#14001E"
            return "#F7F2F8" if sharp else "#4D4154"

        def _blit_sheet(self, r, width, height, st, at):
            if self.state in self.CONFIG_STATES:
                return

            sx, sy = self._sheet_xy()

            panel = renpy.render(self._sheet_panel, self.SHEET_W, self.SHEET_H, st, at)
            r.blit(panel, (sx, sy))

            notes, index, waiting = self._sheet_sequence()

            if waiting or notes is None:
                hint = _("Play a song's opening notes~") if waiting else ""
                if hint:
                    hint_text = renpy.render(
                        Text(
                            hint,
                            font=self.KMP_TXT_OVL_FONT,
                            size=16,
                            color="#C9BDD4",
                            outlines=[],
                        ),
                        self.SHEET_W,
                        self.SHEET_H,
                        st,
                        at,
                    )
                    hw, hh = hint_text.get_size()
                    r.blit(
                        hint_text,
                        (
                            sx + int((self.SHEET_W - hw) / 2),
                            sy + int((self.SHEET_H - hh) / 2),
                        ),
                    )
                return

            if not notes:
                return

            # Page of notes: when this row is finished, the next row replaces it
            page = min(index, max(len(notes) - 1, 0)) // self.WINDOW
            start = page * self.WINDOW
            chunk = notes[start:start + self.WINDOW]
            if not chunk:
                return

            local_idx = index - start
            missing = self.state == self.STATE_MISS

            total_w = (
                len(chunk) * self.TILE_W
                + (len(chunk) - 1) * self.TILE_GAP
            )
            tx = sx + int((self.SHEET_W - total_w) / 2)
            ty = sy + int((self.SHEET_H - self.TILE_H) / 2)

            for i, note in enumerate(chunk):
                if i < local_idx:
                    status = "played"
                elif i == local_idx:
                    status = "miss" if missing else "current"
                else:
                    status = "idle"

                tile = renpy.render(
                    self._tile_for(note, status),
                    self.TILE_W,
                    self.TILE_H,
                    st,
                    at,
                )
                r.blit(tile, (tx, ty))

                letter = renpy.render(
                    Text(
                        self._letter_for_note(note),
                        font=self.KMP_TXT_OVL_FONT,
                        size=22,
                        color=self._letter_color(note, status),
                        outlines=[],
                    ),
                    self.TILE_W,
                    self.TILE_H,
                    st,
                    at,
                )
                lw, lh = letter.get_size()
                r.blit(
                    letter,
                    (
                        tx + int((self.TILE_W - lw) / 2),
                        ty + int((self.TILE_H - lh) / 2),
                    ),
                )

                tx += self.TILE_W + self.TILE_GAP

        def render(self, width, height, st, at):
            r = super(MASPianoSheetDisplayable, self).render(width, height, st, at)
            self._blit_sheet(r, width, height, st, at)
            return r

    # mas_piano_setupstart instantiates PianoDisplayable
    PianoDisplayable = MASPianoSheetDisplayable
